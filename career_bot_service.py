from __future__ import annotations

import argparse
from dataclasses import dataclass

from question_router import QuestionRouter, Route
from unknown_question_repository import UnknownQuestionRepository


@dataclass(frozen=True)
class CareerBotResult:
    route: Route
    response: str
    reason: str
    source_ids: list[str]
    top_score: float | None
    unknown_question_id: str | None


class CareerBotService:
    def __init__(self) -> None:
        self.router = QuestionRouter()
        self.unknown_question_repository = UnknownQuestionRepository()

    def handle_message(
        self,
        *,
        question: str,
        line_user_id: str | None,
        display_name: str | None,
        channel: str | None = None,
    ) -> CareerBotResult:
        router_result = self.router.route(question)
        unknown_question_id: str | None = None

        if router_result.route == Route.HANDOFF:
            unknown_question_id = self.unknown_question_repository.create(
                question=question,
                line_user_id=line_user_id,
                display_name=display_name,
                top_score=router_result.top_score,
                reason=router_result.reason,
                source_ids=router_result.source_ids,
                channel=channel or ("line" if line_user_id else "local_test"),
            )

        return CareerBotResult(
            route=router_result.route,
            response=router_result.response,
            reason=router_result.reason,
            source_ids=router_result.source_ids,
            top_score=router_result.top_score,
            unknown_question_id=unknown_question_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="測試求職 Bot 完整訊息處理流程")
    parser.add_argument("question", nargs="?", help="要測試的問題")
    parser.add_argument("--line-user-id", default=None)
    parser.add_argument("--display-name", default="本機測試")
    args = parser.parse_args()

    question = args.question or input("請輸入測試問題：").strip()
    result = CareerBotService().handle_message(
        question=question,
        line_user_id=args.line_user_id,
        display_name=args.display_name,
    )

    score = f"{result.top_score:.4f}" if result.top_score is not None else "N/A"
    print(f"\nroute: {result.route.value}")
    print(f"top_score: {score}")
    print(f"response: {result.response}")
    print(f"reason: {result.reason}")
    print(f"source_ids: {result.source_ids}")
    print(f"unknown_question_id: {result.unknown_question_id}")


if __name__ == "__main__":
    main()