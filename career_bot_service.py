from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass

from chat_log_repository import ChatLogRepository
from question_router import QuestionRouter, Route
from unknown_question_repository import UnknownQuestionRepository


logger = logging.getLogger(__name__)


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
        self.chat_log_repository: ChatLogRepository | None = None

    def _record_chat_log(
        self,
        *,
        question: str,
        response: str | None,
        route: str | None,
        source_ids: list[str],
        channel: str,
        status: str,
        error_code: str | None = None,
    ) -> None:
        try:
            # Initialization belongs inside the best-effort boundary too.
            if self.chat_log_repository is None:
                self.chat_log_repository = ChatLogRepository()
            self.chat_log_repository.create(
                question=question,
                response=response,
                route=route,
                source_ids=source_ids,
                channel=channel,
                status=status,
                error_code=error_code,
            )
        except Exception:
            # Exception messages can contain request data or credentials.
            logger.warning("Chat log could not be saved; response handling continues.")

    def handle_message(
        self,
        *,
        question: str,
        line_user_id: str | None,
        display_name: str | None,
        channel: str | None = None,
    ) -> CareerBotResult:
        message_channel = channel or ("line" if line_user_id else "local_test")
        router_result = None
        unknown_question_id: str | None = None
        failure_stage = "routing_failed"

        try:
            router_result = self.router.route(question)

            if router_result.route == Route.HANDOFF:
                failure_stage = "handoff_storage_failed"
                # Preserve the separate follow-up queue and its existing identity
                # fields. The new general-purpose log never receives these fields.
                unknown_question_id = self.unknown_question_repository.create(
                    question=question,
                    line_user_id=line_user_id,
                    display_name=display_name,
                    top_score=router_result.top_score,
                    reason=router_result.reason,
                    source_ids=router_result.source_ids,
                    channel=message_channel,
                )
        except Exception:
            self._record_chat_log(
                question=question,
                response=None,
                route=router_result.route.value if router_result is not None else None,
                source_ids=router_result.source_ids if router_result is not None else [],
                channel=message_channel,
                status="error",
                error_code=failure_stage,
            )
            # Preserve existing API/LINE error handling.
            raise

        self._record_chat_log(
            question=question,
            response=router_result.response,
            route=router_result.route.value,
            source_ids=router_result.source_ids,
            channel=message_channel,
            status="success",
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
