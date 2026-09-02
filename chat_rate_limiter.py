from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from google.cloud import firestore


DEFAULT_COLLECTION = "chat_rate_limits"
DEFAULT_LIMIT_PER_HOUR = 20
WINDOW_SECONDS = 60 * 60


class ChatRateLimitExceeded(RuntimeError):
    """同一訪客在目前時段已用完網站 AI 配額。"""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("網站 AI 詢問次數已達上限")
        self.retry_after_seconds = max(1, retry_after_seconds)


class ChatRateLimitUnavailable(RuntimeError):
    """限流設定或 Firestore 暫時無法使用。"""


class ChatRateLimiter:
    """以 Firestore transaction 共用 Cloud Run 多 instance 的每 IP 配額。"""

    def __init__(self) -> None:
        load_dotenv()

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
        if not project_id:
            raise ChatRateLimitUnavailable("缺少 GOOGLE_CLOUD_PROJECT")

        try:
            limit_per_hour = int(
                os.getenv(
                    "CHAT_RATE_LIMIT_PER_HOUR",
                    str(DEFAULT_LIMIT_PER_HOUR),
                )
            )
        except ValueError as error:
            raise ChatRateLimitUnavailable(
                "CHAT_RATE_LIMIT_PER_HOUR 必須是整數"
            ) from error

        if limit_per_hour < 1:
            raise ChatRateLimitUnavailable(
                "CHAT_RATE_LIMIT_PER_HOUR 必須大於 0"
            )

        collection_name = os.getenv(
            "FIRESTORE_CHAT_RATE_LIMIT_COLLECTION",
            DEFAULT_COLLECTION,
        ).strip()
        if not collection_name or "/" in collection_name:
            raise ChatRateLimitUnavailable(
                "FIRESTORE_CHAT_RATE_LIMIT_COLLECTION 必須是有效的 collection 名稱"
            )

        # 建議使用獨立 secret；為了讓既有部署保持相容，未設定時沿用
        # Cloud Run 已有的 LINE secret。secret 只用於 HMAC，不會寫入 Firestore。
        hash_secret = (
            os.getenv("CHAT_RATE_LIMIT_HASH_SECRET", "").strip()
            or os.getenv("LINE_CHANNEL_SECRET", "").strip()
        )
        if not hash_secret:
            raise ChatRateLimitUnavailable(
                "缺少 CHAT_RATE_LIMIT_HASH_SECRET 或 LINE_CHANNEL_SECRET"
            )

        try:
            self.client = firestore.Client(project=project_id)
            self.rate_limits = self.client.collection(collection_name)
        except Exception as error:
            raise ChatRateLimitUnavailable(
                "無法初始化 Firestore 限流儲存"
            ) from error

        self.limit_per_hour = limit_per_hour
        self.hash_secret = hash_secret

    def reserve(self, remote_ip: str) -> None:
        """原子地保留一次額度；超限或儲存失敗時拒絕請求。"""

        if not isinstance(remote_ip, str) or not remote_ip.strip():
            raise ChatRateLimitUnavailable("無法辨識訪客來源")

        now = datetime.now(timezone.utc)
        now_seconds = int(now.timestamp())
        window_number = now_seconds // WINDOW_SECONDS
        retry_after_seconds = max(
            1,
            ((window_number + 1) * WINDOW_SECONDS) - now_seconds,
        )
        visitor_id = hmac.new(
            self.hash_secret.encode("utf-8"),
            remote_ip.strip().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        rate_reference = self.rate_limits.document(visitor_id)

        @firestore.transactional
        def reserve_rate_limit(transaction) -> None:
            snapshot = rate_reference.get(transaction=transaction)
            stored = snapshot.to_dict() if snapshot.exists else {}
            stored = stored or {}
            is_current_window = stored.get("window_number") == window_number
            count = int(stored.get("count", 0)) if is_current_window else 0

            if count >= self.limit_per_hour:
                raise ChatRateLimitExceeded(retry_after_seconds)

            transaction.set(
                rate_reference,
                {
                    "count": count + 1,
                    "window_number": window_number,
                    "window_started_at": datetime.fromtimestamp(
                        window_number * WINDOW_SECONDS,
                        tz=timezone.utc,
                    ),
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=False,
            )

        try:
            reserve_rate_limit(self.client.transaction())
        except ChatRateLimitExceeded:
            raise
        except Exception as error:
            raise ChatRateLimitUnavailable(
                "Firestore 限流交易失敗"
            ) from error


@lru_cache(maxsize=1)
def get_chat_rate_limiter() -> ChatRateLimiter:
    return ChatRateLimiter()
