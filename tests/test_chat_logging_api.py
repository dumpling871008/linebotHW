import os
from unittest.mock import Mock

import pytest

os.environ.setdefault("LINE_CHANNEL_SECRET", "test-channel-secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-channel-access-token")

import app as app_module  # noqa: E402
from career_bot_service import CareerBotService  # noqa: E402
from question_router import Route, RouterResult  # noqa: E402


@pytest.fixture
def service(monkeypatch):
    instance = CareerBotService.__new__(CareerBotService)
    instance.router = Mock()
    instance.unknown_question_repository = Mock()
    instance.chat_log_repository = Mock()
    monkeypatch.setattr(
        app_module, "get_career_bot_service", Mock(return_value=instance)
    )
    return instance


@pytest.mark.parametrize("route", list(Route))
def test_chat_api_logs_each_route_and_preserves_response(service, route) -> None:
    sources = ["01_profile.001"] if route == Route.ANSWER else []
    service.router.route.return_value = RouterResult(
        route=route,
        response="測試回覆",
        reason="測試原因",
        source_ids=sources,
        top_score=0.82,
    )
    client = app_module.app.test_client()
    origin = app_module.cors_allowed_origins[0]
    response = client.post(
        "/api/chat",
        json={"question": " 問題內容 "},
        headers={"Origin": origin},
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "response": "測試回覆",
        "route": route.value,
        "source_ids": sources,
    }
    assert response.headers["Access-Control-Allow-Origin"] == origin
    service.chat_log_repository.create.assert_called_once_with(
        question="問題內容",
        response="測試回覆",
        route=route.value,
        source_ids=sources,
        channel="website",
        status="success",
        error_code=None,
    )


def test_chat_api_still_responds_if_logging_fails(service) -> None:
    service.router.route.return_value = RouterResult(
        route=Route.ANSWER,
        response="正常回覆",
        reason="測試",
        source_ids=["01_profile.001"],
        top_score=0.82,
    )
    service.chat_log_repository.create.side_effect = TimeoutError("storage down")
    response = app_module.app.test_client().post(
        "/api/chat", json={"question": "問題"}
    )
    assert response.status_code == 200
    assert response.get_json()["response"] == "正常回覆"


def test_failed_model_request_is_logged_without_changing_api_error(service) -> None:
    service.router.route.side_effect = RuntimeError("model unavailable")
    response = app_module.app.test_client().post(
        "/api/chat", json={"question": "問題"}
    )
    assert response.status_code == 503
    record = service.chat_log_repository.create.call_args.kwargs
    assert record["question"] == "問題"
    assert record["response"] is None
    assert record["status"] == "error"
    assert record["error_code"] == "routing_failed"


def test_invalid_requests_and_preflight_are_not_logged(service) -> None:
    client = app_module.app.test_client()
    assert client.options("/api/chat").status_code == 204
    assert client.post("/api/chat", data="not-json").status_code == 400
    assert client.post("/api/chat", json={}).status_code == 400
    assert client.post("/api/chat", json={"question": "  "}).status_code == 400
    assert client.post("/api/chat", json={"question": "問" * 501}).status_code == 400
    service.router.route.assert_not_called()
    service.chat_log_repository.create.assert_not_called()


def test_no_public_log_listing_route() -> None:
    assert app_module.app.test_client().get("/api/chat-logs").status_code == 404
