from unittest.mock import Mock

import pytest

import website_message_service as message_module


VALID_PAYLOAD = {
    "name": " 王小明 ",
    "email": " HELLO@Example.com ",
    "topic": "collaboration",
    "message": " 想和你聊聊一個資料平台合作機會。 ",
    "website": "",
    "turnstile_token": "verified-token",
}


def test_validate_message_payload_normalizes_fields() -> None:
    message = message_module.validate_message_payload(VALID_PAYLOAD)

    assert message.name == "王小明"
    assert message.email == "hello@example.com"
    assert message.topic == "collaboration"
    assert message.message == "想和你聊聊一個資料平台合作機會。"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("email", "not-an-email"),
        ("topic", "unknown"),
        ("message", "太短"),
        ("turnstile_token", ""),
    ],
)
def test_validate_message_payload_rejects_invalid_fields(
    field: str,
    value: str,
) -> None:
    payload = {**VALID_PAYLOAD, field: value}

    with pytest.raises(message_module.WebsiteMessageValidationError):
        message_module.validate_message_payload(payload)


def test_honeypot_submission_is_not_verified_or_stored(monkeypatch) -> None:
    repository = Mock()
    verifier = Mock()
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "secret")
    service = message_module.WebsiteMessageService(
        cors_origins=["https://portfolio.example.com"],
        repository=repository,
        verifier=verifier,
    )

    result = service.submit(
        {**VALID_PAYLOAD, "website": "https://spam.example.com"},
        "203.0.113.8",
    )

    assert result is None
    verifier.verify.assert_not_called()
    repository.create.assert_not_called()


def test_submit_verifies_and_stores_without_raw_ip(monkeypatch) -> None:
    repository = Mock()
    repository.create.return_value = "message-id"
    verifier = Mock()
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "secret")
    service = message_module.WebsiteMessageService(
        cors_origins=["https://portfolio.example.com"],
        repository=repository,
        verifier=verifier,
    )

    result = service.submit(VALID_PAYLOAD, "203.0.113.8")

    assert result == "message-id"
    verifier.verify.assert_called_once_with(
        "verified-token",
        "203.0.113.8",
    )
    stored_message, visitor_hash = repository.create.call_args.args
    assert stored_message.email == "hello@example.com"
    assert visitor_hash != "203.0.113.8"
    assert len(visitor_hash) == 64


def test_turnstile_verifier_accepts_expected_hostname_and_action(
    monkeypatch,
) -> None:
    response = Mock()
    response.json.return_value = {
        "success": True,
        "hostname": "portfolio.example.com",
        "action": "contact",
    }
    monkeypatch.setattr(message_module.requests, "post", Mock(return_value=response))
    verifier = message_module.TurnstileVerifier(
        "secret",
        {"portfolio.example.com"},
    )

    verifier.verify("token", "203.0.113.8")

    response.raise_for_status.assert_called_once_with()


def test_turnstile_verifier_rejects_unexpected_hostname(monkeypatch) -> None:
    response = Mock()
    response.json.return_value = {
        "success": True,
        "hostname": "untrusted.example.com",
        "action": "contact",
    }
    monkeypatch.setattr(message_module.requests, "post", Mock(return_value=response))
    verifier = message_module.TurnstileVerifier(
        "secret",
        {"portfolio.example.com"},
    )

    with pytest.raises(message_module.WebsiteMessageValidationError):
        verifier.verify("token", "203.0.113.8")


def test_parse_allowed_hostnames_defaults_to_cors_origins() -> None:
    assert message_module.parse_allowed_hostnames(
        None,
        ["https://portfolio.example.com", "http://localhost:4321"],
    ) == {"portfolio.example.com", "localhost"}
