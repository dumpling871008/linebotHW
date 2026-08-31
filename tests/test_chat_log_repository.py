from unittest.mock import Mock

import pytest

import chat_log_repository as log_module


@pytest.fixture
def repository(monkeypatch):
    monkeypatch.setattr(log_module, "load_dotenv", Mock())
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.delenv("FIRESTORE_CHAT_LOG_COLLECTION", raising=False)
    client = Mock()
    client.collection.return_value.document.return_value.id = "chat-log-123"
    monkeypatch.setattr(log_module.firestore, "Client", Mock(return_value=client))
    return log_module.ChatLogRepository()


def test_default_collection_and_server_project(repository) -> None:
    log_module.firestore.Client.assert_called_once_with(project="test-project")
    repository.client.collection.assert_called_once_with("chat_logs")


@pytest.mark.parametrize(
    ("configured", "expected"),
    [(" custom_logs ", "custom_logs"), (" ", "chat_logs")],
)
def test_configured_collection(repository, monkeypatch, configured, expected) -> None:
    monkeypatch.setenv("FIRESTORE_CHAT_LOG_COLLECTION", configured)
    instance = log_module.ChatLogRepository()
    instance.client.collection.assert_called_with(expected)


def test_missing_project_fails_without_creating_client(monkeypatch) -> None:
    monkeypatch.setattr(log_module, "load_dotenv", Mock())
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    client_factory = Mock()
    monkeypatch.setattr(log_module.firestore, "Client", client_factory)
    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        log_module.ChatLogRepository()
    client_factory.assert_not_called()


def test_collection_cannot_be_nested(repository, monkeypatch) -> None:
    monkeypatch.setenv("FIRESTORE_CHAT_LOG_COLLECTION", "logs/document/nested")
    with pytest.raises(ValueError, match="單一集合"):
        log_module.ChatLogRepository()


def test_stores_only_requested_fields_with_timestamp_and_bounded_write(repository) -> None:
    log_id = repository.create(
        question="  請介紹君璇  ",
        response="公開的回覆",
        route="ANSWER",
        source_ids=["01_profile.001"],
        channel="website",
        status="success",
    )
    assert log_id == "chat-log-123"
    reference = repository.collection.document.return_value
    repository.collection.document.assert_called_once_with()
    reference.set.assert_called_once_with(
        {
            "question": "請介紹君璇",
            "response": "公開的回覆",
            "route": "ANSWER",
            "source_ids": ["01_profile.001"],
            "channel": "website",
            "status": "success",
            "error_code": None,
            "created_at": log_module.firestore.SERVER_TIMESTAMP,
        },
        retry=None,
        timeout=2.0,
    )


def test_blank_question_is_not_stored(repository) -> None:
    with pytest.raises(ValueError, match="不可為空白"):
        repository.create(
            question="   ",
            response=None,
            route=None,
            source_ids=[],
            channel="website",
            status="error",
        )
    repository.collection.document.assert_not_called()


def test_error_record_does_not_invent_an_answer(repository) -> None:
    repository.create(
        question="問題",
        response=None,
        route=None,
        source_ids=[],
        channel="website",
        status="error",
        error_code="routing_failed",
    )
    payload = repository.collection.document.return_value.set.call_args.args[0]
    assert payload["response"] is None
    assert payload["route"] is None
    assert payload["status"] == "error"
    assert payload["error_code"] == "routing_failed"


def test_write_failure_is_raised_for_service_to_handle(repository) -> None:
    reference = repository.collection.document.return_value
    reference.set.side_effect = TimeoutError("Firestore timeout")
    with pytest.raises(TimeoutError):
        repository.create(
            question="問題",
            response="回覆",
            route="ANSWER",
            source_ids=["01_profile.001"],
            channel="website",
            status="success",
        )
    assert reference.set.call_count == 1
