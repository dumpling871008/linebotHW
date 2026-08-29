from unittest.mock import Mock

import pytest

from career_bot_service import CareerBotService
from question_router import Route, RouterResult


def make_service(router_result: RouterResult) -> CareerBotService:
    service = CareerBotService.__new__(CareerBotService)
    service.router = Mock()
    service.router.route.return_value = router_result
    service.unknown_question_repository = Mock()
    return service


@pytest.mark.parametrize("route", [Route.ANSWER, Route.OUT_OF_SCOPE])
def test_non_handoff_route_does_not_write_firestore(route: Route) -> None:
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
