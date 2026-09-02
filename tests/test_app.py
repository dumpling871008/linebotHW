import os
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest


os.environ.setdefault("LINE_CHANNEL_SECRET", "test-channel-secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-channel-access-token")

import app as app_module  # noqa: E402


@pytest.fixture(autouse=True)
def chat_rate_limiter(monkeypatch):
    limiter = Mock()
    monkeypatch.setattr(
        app_module,
        "get_chat_rate_limiter",
        Mock(return_value=limiter),
    )
    return limiter


def test_parse_cors_allowed_origins_supports_multiple_origins() -> None:
    assert app_module.parse_cors_allowed_origins(
        " https://portfolio.example.com/, http://localhost:4321, "
        "https://portfolio.example.com "
    ) == [
        "https://portfolio.example.com",
        "http://localhost:4321",
    ]


def test_parse_cors_allowed_origins_rejects_wildcard() -> None:
    with pytest.raises(ValueError, match="不可使用 \\*"):
        app_module.parse_cors_allowed_origins("https://example.com,*")


def test_get_line_display_name() -> None:
    messaging_api = Mock()
    messaging_api.get_profile.return_value = SimpleNamespace(
        display_name=" 招募小編 "
    )

    display_name = app_module.get_line_display_name(messaging_api, "U123")

    assert display_name == "招募小編"
    messaging_api.get_profile.assert_called_once_with("U123")


def test_get_line_display_name_failure_returns_none() -> None:
    messaging_api = Mock()
    messaging_api.get_profile.side_effect = RuntimeError("profile unavailable")

    display_name = app_module.get_line_display_name(messaging_api, "U123")

    assert display_name is None


def test_handle_text_message_uses_profile_and_career_service(monkeypatch) -> None:
    service = Mock()
    service.handle_message.return_value = SimpleNamespace(
        route=SimpleNamespace(value="ANSWER"),
        response="知識庫回答",
        source_ids=["01_profile.001"],
        unknown_question_id=None,
    )
    messaging_api = Mock()
    messaging_api.get_profile.return_value = SimpleNamespace(
        display_name="招募小編"
    )
    api_client_context = MagicMock()

    monkeypatch.setattr(
        app_module,
        "get_career_bot_service",
        Mock(return_value=service),
    )
    monkeypatch.setattr(
        app_module,
        "ApiClient",
        Mock(return_value=api_client_context),
    )
    monkeypatch.setattr(
        app_module,
        "MessagingApi",
        Mock(return_value=messaging_api),
    )

    event = SimpleNamespace(
        message=SimpleNamespace(text=" 請介紹林君璇 "),
        source=SimpleNamespace(user_id="U123"),
        reply_token="reply-token",
    )

    app_module.handle_text_message(event)

    service.handle_message.assert_called_once_with(
        question="請介紹林君璇",
        line_user_id="U123",
        display_name="招募小編",
    )
    reply_request = messaging_api.reply_message.call_args.args[0]
    assert reply_request.reply_token == "reply-token"
    assert reply_request.messages[0].text == "知識庫回答"


def test_flask_routes() -> None:
    client = app_module.app.test_client()

    assert client.get("/").status_code == 200
    assert client.post("/callback", data="{}").status_code == 400


def test_chat_api_uses_existing_career_service(
    monkeypatch,
    chat_rate_limiter,
) -> None:
    service = Mock()
    service.handle_message.return_value = SimpleNamespace(
        route=SimpleNamespace(value="ANSWER"),
        response="網站知識庫回答",
        source_ids=["01_profile.001"],
    )
    monkeypatch.setattr(
        app_module,
        "get_career_bot_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()
    allowed_origin = app_module.cors_allowed_origins[0]

    response = client.post(
        "/api/chat",
        json={"question": " 請介紹林君璇 "},
        headers={
            "Origin": allowed_origin,
            "X-Forwarded-For": "198.51.100.4, 203.0.113.8, 10.0.0.1",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "response": "網站知識庫回答",
        "route": "ANSWER",
        "source_ids": ["01_profile.001"],
    }
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    chat_rate_limiter.reserve.assert_called_once_with("203.0.113.8")
    service.handle_message.assert_called_once_with(
        question="請介紹林君璇",
        line_user_id=None,
        display_name=None,
        channel="website",
    )


def test_chat_api_allows_json_preflight_for_configured_origin() -> None:
    client = app_module.app.test_client()
    allowed_origin = app_module.cors_allowed_origins[0]

    response = client.options(
        "/api/chat",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "content-type" in response.headers[
        "Access-Control-Allow-Headers"
    ].lower()


def test_chat_api_does_not_allow_unconfigured_origin() -> None:
    client = app_module.app.test_client()

    response = client.options(
        "/api/chat",
        headers={
            "Origin": "https://untrusted.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 204
    assert "Access-Control-Allow-Origin" not in response.headers


def test_chat_api_rejects_invalid_json_and_question(chat_rate_limiter) -> None:
    client = app_module.app.test_client()

    assert client.post("/api/chat", data="not-json").status_code == 400
    assert client.post("/api/chat", json={}).status_code == 400
    assert client.post("/api/chat", json={"question": "   "}).status_code == 400
    assert client.post(
        "/api/chat",
        json={"question": "問" * 501},
    ).status_code == 400
    chat_rate_limiter.reserve.assert_not_called()


def test_chat_api_returns_429_before_calling_service(
    monkeypatch,
    chat_rate_limiter,
) -> None:
    chat_rate_limiter.reserve.side_effect = (
        app_module.ChatRateLimitExceeded(1234)
    )
    service = Mock()
    monkeypatch.setattr(
        app_module,
        "get_career_bot_service",
        Mock(return_value=service),
    )

    response = app_module.app.test_client().post(
        "/api/chat",
        json={"question": "請介紹林君璇"},
    )

    assert response.status_code == 429
    assert response.get_json() == {
        "error": "詢問次數已達上限，請稍後再試。"
    }
    assert response.headers["Retry-After"] == "1234"
    service.handle_message.assert_not_called()


def test_chat_api_fails_closed_when_rate_limiter_is_unavailable(
    monkeypatch,
    chat_rate_limiter,
) -> None:
    chat_rate_limiter.reserve.side_effect = (
        app_module.ChatRateLimitUnavailable("Firestore unavailable")
    )
    service = Mock()
    monkeypatch.setattr(
        app_module,
        "get_career_bot_service",
        Mock(return_value=service),
    )

    response = app_module.app.test_client().post(
        "/api/chat",
        json={"question": "請介紹林君璇"},
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "AI 服務暫時無法使用，請稍後再試。"
    }
    service.handle_message.assert_not_called()


def test_chat_api_returns_503_when_service_fails(monkeypatch) -> None:
    service = Mock()
    service.handle_message.side_effect = RuntimeError("service unavailable")
    monkeypatch.setattr(
        app_module,
        "get_career_bot_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()

    response = client.post("/api/chat", json={"question": "請介紹林君璇"})

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "AI 服務暫時無法使用，請稍後再試。"
    }


def test_message_api_stores_private_message(monkeypatch) -> None:
    service = Mock()
    service.submit.return_value = "message-document-id"
    monkeypatch.setattr(
        app_module,
        "get_website_message_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()
    allowed_origin = app_module.cors_allowed_origins[0]

    response = client.post(
        "/api/messages",
        json={
            "name": "王小明",
            "email": "hello@example.com",
            "topic": "collaboration",
            "message": "想和你聊聊一個資料平台合作機會。",
            "website": "",
            "turnstile_token": "verified-token",
        },
        headers={
            "Origin": allowed_origin,
            "X-Forwarded-For": "198.51.100.4, 203.0.113.8, 10.0.0.1",
        },
    )

    assert response.status_code == 201
    assert response.get_json() == {"message": "留言已送出，謝謝你！"}
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    service.submit.assert_called_once()
    assert service.submit.call_args.args[1] == "203.0.113.8"


def test_message_api_allows_json_preflight() -> None:
    client = app_module.app.test_client()
    allowed_origin = app_module.cors_allowed_origins[0]

    response = client.options(
        "/api/messages",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "content-type" in response.headers[
        "Access-Control-Allow-Headers"
    ].lower()


def test_message_api_returns_validation_error(monkeypatch) -> None:
    service = Mock()
    service.submit.side_effect = app_module.WebsiteMessageValidationError(
        "請輸入有效的 Email。"
    )
    monkeypatch.setattr(
        app_module,
        "get_website_message_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()

    response = client.post("/api/messages", json={"email": "wrong"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "請輸入有效的 Email。"}


def test_message_api_rate_limit(monkeypatch) -> None:
    service = Mock()
    service.submit.side_effect = app_module.WebsiteMessageRateLimitExceeded
    monkeypatch.setattr(
        app_module,
        "get_website_message_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()

    response = client.post("/api/messages", json={})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "3600"


def test_message_api_service_unavailable(monkeypatch) -> None:
    service = Mock()
    service.submit.side_effect = app_module.WebsiteMessageServiceUnavailable(
        "Firestore unavailable"
    )
    monkeypatch.setattr(
        app_module,
        "get_website_message_service",
        Mock(return_value=service),
    )
    client = app_module.app.test_client()

    response = client.post("/api/messages", json={})

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "留言服務暫時無法使用，請稍後再試。"
    }
