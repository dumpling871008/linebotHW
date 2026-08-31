from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import firestore


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_COLLECTION = "chat_logs"
WRITE_TIMEOUT_SECONDS = 2.0


class ChatLogRepository:
    """Server-only question logs; no visitor identifiers or public read API."""

    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise RuntimeError("缺少 GOOGLE_CLOUD_PROJECT")

        collection_name = (
            os.getenv("FIRESTORE_CHAT_LOG_COLLECTION", "").strip()
            or DEFAULT_COLLECTION
        )
        if "/" in collection_name:
            raise ValueError("FIRESTORE_CHAT_LOG_COLLECTION 必須是單一集合名稱")

        self.client = firestore.Client(project=project_id)
        self.collection = self.client.collection(collection_name)

    def create(
        self,
        *,
        question: str,
        response: str | None,
        route: str | None,
        source_ids: list[str],
        channel: str,
        status: str,
        error_code: str | None = None,
    ) -> str:
        question = question.strip()
        if not question:
            raise ValueError("問題不可為空白")

        document = {
            "question": question,
            "response": response,
            "route": route,
            "source_ids": list(source_ids),
            "channel": channel,
            "status": status,
            "error_code": error_code,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        reference = self.collection.document()
        # Complete the write before returning; do not rely on background threads
        # remaining alive after a Cloud Run response. Bound the Firestore RPC.
        reference.set(document, retry=None, timeout=WRITE_TIMEOUT_SECONDS)
        return reference.id
