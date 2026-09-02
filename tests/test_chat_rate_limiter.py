import hashlib
import hmac
import os
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

import chat_rate_limiter as rate_module


@pytest.fixture
def limiter_dependencies(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "line-fallback-secret")
    monkeypatch.delenv("CHAT_RATE_LIMIT_HASH_SECRET", raising=False)
    monkeypatch.delenv("CHAT_RATE_LIMIT_PER_HOUR", raising=False)
    monkeypatch.delenv(
        "FIRESTORE_CHAT_RATE_LIMIT_COLLECTION",
        raising=False,
    )
    monkeypatch.setattr(rate_module, "load_dotenv", Mock())
    monkeypatch.setattr(
        rate_module.firestore,
        "transactional",
        lambda function: function,
    )

    client = Mock()
    collection = Mock()
    reference = Mock()
    transaction = Mock()
    client.collection.return_value = collection
    collection.document.return_value = reference
    client.transaction.return_value = transaction
    monkeypatch.setattr(
        rate_module.firestore,
        "Client",
        Mock(return_value=client),
    )
    return client, collection, reference, transaction


def test_uses_defaults_and_hmac_document_id(limiter_dependencies) -> None:
    client, collection, reference, transaction = limiter_dependencies
    reference.get.return_value = Mock(exists=False)
    remote_ip = "203.0.113.8"

    limiter = rate_module.ChatRateLimiter()
    limiter.reserve(remote_ip)

    rate_module.firestore.Client.assert_called_once_with(
        project="test-project"
    )
    client.collection.assert_called_once_with("chat_rate_limits")
    expected_id = hmac.new(
        b"line-fallback-secret",
        remote_ip.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    collection.document.assert_called_once_with(expected_id)
    payload = transaction.set.call_args.args[1]
    assert payload["count"] == 1
    assert payload["window_number"] == (
        int(datetime.now(timezone.utc).timestamp())
        // rate_module.WINDOW_SECONDS
    )
    assert remote_ip not in str(payload)
    assert transaction.set.call_args.kwargs == {"merge": False}


def test_rejects_request_when_current_window_is_full(
    limiter_dependencies,
    monkeypatch,
) -> None:
    _, _, reference, transaction = limiter_dependencies
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_HOUR", "2")
    current_window = (
        int(datetime.now(timezone.utc).timestamp())
        // rate_module.WINDOW_SECONDS
    )
    snapshot = Mock(exists=True)
    snapshot.to_dict.return_value = {
        "count": 2,
        "window_number": current_window,
    }
    reference.get.return_value = snapshot

    limiter = rate_module.ChatRateLimiter()
    with pytest.raises(rate_module.ChatRateLimitExceeded) as error:
        limiter.reserve("203.0.113.8")

    assert 1 <= error.value.retry_after_seconds <= 3600
    transaction.set.assert_not_called()


def test_new_hour_resets_existing_counter(limiter_dependencies) -> None:
    _, _, reference, transaction = limiter_dependencies
    current_window = (
        int(datetime.now(timezone.utc).timestamp())
        // rate_module.WINDOW_SECONDS
    )
    snapshot = Mock(exists=True)
    snapshot.to_dict.return_value = {
        "count": 999,
        "window_number": current_window - 1,
    }
    reference.get.return_value = snapshot

    rate_module.ChatRateLimiter().reserve("203.0.113.8")

    assert transaction.set.call_args.args[1]["count"] == 1


@pytest.mark.parametrize("configured_limit", ["wrong", "0", "-1"])
def test_rejects_invalid_limit_configuration(
    limiter_dependencies,
    monkeypatch,
    configured_limit,
) -> None:
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_HOUR", configured_limit)

    with pytest.raises(rate_module.ChatRateLimitUnavailable):
        rate_module.ChatRateLimiter()


def test_wraps_firestore_failure_as_unavailable(
    limiter_dependencies,
) -> None:
    _, _, reference, _ = limiter_dependencies
    reference.get.side_effect = TimeoutError("Firestore timeout")

    with pytest.raises(rate_module.ChatRateLimitUnavailable):
        rate_module.ChatRateLimiter().reserve("203.0.113.8")
