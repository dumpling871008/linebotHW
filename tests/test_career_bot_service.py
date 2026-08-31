from unittest.mock import Mock

import pytest

import career_bot_service as service_module

from career_bot_service import CareerBotService
from question_router import Route, RouterResult


def make_service(router_result: RouterResult) -> CareerBotService:
    service = CareerBotService.__new__(CareerBotService)
    service.router = Mock()
    service.router.route.return_value = router_result
    service.unknown_question_repository = Mock()
    service.chat_log_repository = Mock()
    return service


@pytest.mark.parametrize("route", [Route.ANSWER, Route.OUT_OF_SCOPE])
def test_non_handoff_route_does_not_write_followup_queue(route: Route) -> None:
    service = make_service(
        RouterResult(
            route=route,
            response="測試回覆",
            reason="測試原因",
            source_ids=["01_profile.001"] if route == Route.ANSWER else [],
            top_score=0.82,
        )
    )

    result = service.handle_message(
        question="請介紹林君璇",
        line_user_id="U123",
        display_name="招募小編",
    )

    assert result.route == route
    assert result.response == "測試回覆"
    assert result.unknown_question_id is None
    service.unknown_question_repository.create.assert_not_called()


def test_handoff_route_writes_firestore() -> None:
    service = make_service(
        RouterResult(
            route=Route.HANDOFF,
            response="已記錄並轉交本人",
            reason="需要本人確認",
            source_ids=[],
            top_score=0.61,
        )
    )
    service.unknown_question_repository.create.return_value = "document-123"

    result = service.handle_message(
        question="她期望薪資是多少？",
        line_user_id="U123",
        display_name="招募小編",
    )

    assert result.route == Route.HANDOFF
    assert result.unknown_question_id == "document-123"
    service.unknown_question_repository.create.assert_called_once_with(
        question="她期望薪資是多少？",
        line_user_id="U123",
        display_name="招募小編",
        top_score=0.61,
        reason="需要本人確認",
        source_ids=[],
        channel="line",
    )


@pytest.mark.parametrize("route", list(Route))
@pytest.mark.parametrize(
    ("channel", "line_user_id", "expected_channel"),
    [
        ("website", None, "website"),
        (None, "U-private", "line"),
        (None, None, "local_test"),
    ],
)
def test_all_routes_are_logged_without_visitor_identifiers(
    route: Route,
    channel: str | None,
    line_user_id: str | None,
    expected_channel: str,
) -> None:
    source_ids = ["01_profile.001"] if route == Route.ANSWER else []
    service = make_service(
        RouterResult(
            route=route,
            response="測試回覆",
            reason="測試原因",
            source_ids=source_ids,
            top_score=0.82,
        )
    )
    result = service.handle_message(
        question="請介紹君璇",
        line_user_id=line_user_id,
        display_name="不可存到一般紀錄的姓名",
        channel=channel,
    )
    service.chat_log_repository.create.assert_called_once_with(
        question="請介紹君璇",
        response="測試回覆",
        route=route.value,
        source_ids=source_ids,
        channel=expected_channel,
        status="success",
        error_code=None,
    )
    assert result.response == "測試回覆"


@pytest.mark.parametrize("route", list(Route))
def test_log_write_failure_does_not_change_answer(route: Route, caplog) -> None:
    service = make_service(
        RouterResult(
            route=route,
            response="仍可正常回答",
            reason="測試",
            source_ids=["01_profile.001"] if route == Route.ANSWER else [],
            top_score=0.82,
        )
    )
    service.chat_log_repository.create.side_effect = RuntimeError(
        "secret-token-and-private-question"
    )
    result = service.handle_message(
        question="private-question",
        line_user_id=None,
        display_name=None,
        channel="website",
    )
    assert result.route == route
    assert result.response == "仍可正常回答"
    assert "Chat log could not be saved" in caplog.text
    assert "secret-token" not in caplog.text
    assert "private-question" not in caplog.text


def test_log_initialization_failure_does_not_change_answer(monkeypatch) -> None:
    service = make_service(
        RouterResult(
            route=Route.ANSWER,
            response="正常回答",
            reason="測試",
            source_ids=["01_profile.001"],
            top_score=0.82,
        )
    )
    service.chat_log_repository = None
    monkeypatch.setattr(
        service_module,
        "ChatLogRepository",
        Mock(side_effect=RuntimeError("credentials unavailable")),
    )
    result = service.handle_message(
        question="請介紹君璇",
        line_user_id=None,
        display_name=None,
    )
    assert result.response == "正常回答"


def test_service_does_not_initialize_log_client_at_startup(monkeypatch) -> None:
    monkeypatch.setattr(service_module, "QuestionRouter", Mock())
    monkeypatch.setattr(service_module, "UnknownQuestionRepository", Mock())
    log_factory = Mock()
    monkeypatch.setattr(service_module, "ChatLogRepository", log_factory)
    service = CareerBotService()
    assert service.chat_log_repository is None
    log_factory.assert_not_called()


def test_router_failure_is_logged_and_original_error_is_preserved() -> None:
    service = make_service(
        RouterResult(
            route=Route.ANSWER,
            response="",
            reason="",
            source_ids=[],
            top_score=None,
        )
    )
    failure = RuntimeError("private model error")
    service.router.route.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        service.handle_message(
            question="使用者問題",
            line_user_id=None,
            display_name=None,
            channel="website",
        )
    assert error.value is failure
    service.chat_log_repository.create.assert_called_once_with(
        question="使用者問題",
        response=None,
        route=None,
        source_ids=[],
        channel="website",
        status="error",
        error_code="routing_failed",
    )
    service.unknown_question_repository.create.assert_not_called()


def test_handoff_storage_failure_is_logged_and_preserved() -> None:
    service = make_service(
        RouterResult(
            route=Route.HANDOFF,
            response="需本人確認",
            reason="資料不足",
            source_ids=[],
            top_score=0.4,
        )
    )
    failure = RuntimeError("follow-up storage unavailable")
    service.unknown_question_repository.create.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        service.handle_message(
            question="需要本人確認的問題",
            line_user_id=None,
            display_name=None,
            channel="website",
        )
    assert error.value is failure
    service.chat_log_repository.create.assert_called_once_with(
        question="需要本人確認的問題",
        response=None,
        route="HANDOFF",
        source_ids=[],
        channel="website",
        status="error",
        error_code="handoff_storage_failed",
    )


def test_log_failure_does_not_mask_router_failure() -> None:
    service = make_service(
        RouterResult(
            route=Route.ANSWER,
            response="",
            reason="",
            source_ids=[],
            top_score=None,
        )
    )
    original_error = RuntimeError("routing unavailable")
    service.router.route.side_effect = original_error
    service.chat_log_repository.create.side_effect = RuntimeError("log unavailable")
    with pytest.raises(RuntimeError) as error:
        service.handle_message(
            question="測試問題",
            line_user_id=None,
            display_name=None,
        )
    assert error.value is original_error
