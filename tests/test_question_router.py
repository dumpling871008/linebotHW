import json
from types import SimpleNamespace
from unittest.mock import Mock

from question_router import HANDOFF_RESPONSE, QuestionRouter, Route
from rag_service import RetrievalResult


def make_router(model_decision: dict) -> QuestionRouter:
    router = QuestionRouter.__new__(QuestionRouter)
    router.model = "test-model"
    router.answer_policy = "只能根據知識庫回答。"
    router.rag_service = Mock()
    router.rag_service.retrieve.return_value = [
        RetrievalResult(
            source_id="01_profile.001",
            source="01_profile.md",
            section="基本資料",
            content="林君璇畢業於中原大學心理學系。",
            score=0.82,
        )
    ]
    router.client = Mock()
    router.client.models.generate_content.return_value = SimpleNamespace(
        text=json.dumps(model_decision, ensure_ascii=False)
    )
    return router


def test_answer_with_valid_source_is_returned() -> None:
    router = make_router(
        {
            "route": "ANSWER",
            "response": "林君璇畢業於中原大學心理學系。",
            "reason": "知識庫有明確資料",
            "source_ids": ["01_profile.001"],
        }
    )

    result = router.route("她畢業於哪裡？")

    assert result.route == Route.ANSWER
    assert result.source_ids == ["01_profile.001"]
    assert result.top_score == 0.82


def test_answer_with_invalid_source_is_forced_to_handoff() -> None:
    router = make_router(
        {
            "route": "ANSWER",
            "response": "無法驗證的回答",
            "reason": "模型聲稱有資料",
            "source_ids": ["invented.999"],
        }
    )

    result = router.route("她畢業於哪裡？")

    assert result.route == Route.HANDOFF
    assert result.response == HANDOFF_RESPONSE
    assert result.source_ids == []
