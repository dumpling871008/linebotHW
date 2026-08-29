from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import firestore


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_COLLECTION = "unknown_questions"


class UnknownQuestionRepository:
    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        collection_name = os.getenv(
            "FIRESTORE_UNKNOWN_QUESTION_COLLECTION",
            DEFAULT_COLLECTION,
        )

        if not project_id:
            raise RuntimeError(".env 缺少 GOOGLE_CLOUD_PROJECT")

        self.client = firestore.Client(project=project_id)
        self.collection = self.client.collection(collection_name)

    def create(
        self,
        *,
        question: str,
        line_user_id: str | None,
        display_name: str | None,
        top_score: float | None,
        reason: str,
        source_ids: list[str] | None = None,
        channel: str = "line",
    ) -> str:
        question = question.strip()
        if not question:
            raise ValueError("問題不可為空白")

        document = {
            "question": question,
            "line_user_id": line_user_id,
            "display_name": display_name,
            "top_score": top_score,
            "reason": reason.strip(),
            "source_ids": source_ids or [],
            "route": "HANDOFF",
            "status": "pending",
            "channel": channel,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        document_reference = self.collection.document()
        document_reference.set(document)
        return document_reference.id


def main() -> None:
    parser = argparse.ArgumentParser(description="測試 Firestore 未知問題寫入")
    parser.add_argument("question", nargs="?", help="要記錄的問題")
    args = parser.parse_args()

    question = args.question or input("請輸入要記錄的測試問題：").strip()
    repository = UnknownQuestionRepository()
    document_id = repository.create(
        question=question,
        line_user_id="local-test-user",
        display_name="本機測試",
        top_score=0.6744,
        reason="本機測試：問題需要由本人確認。",
        source_ids=[],
        channel="local_test",
    )

    print("Firestore 寫入成功")
    print(f"collection: {DEFAULT_COLLECTION}")
    print(f"document_id: {document_id}")


if __name__ == "__main__":
    main()