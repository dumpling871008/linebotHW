from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv
from google.cloud import firestore


DEFAULT_MESSAGE_COLLECTION = "website_messages"
DEFAULT_RATE_LIMIT_COLLECTION = "website_message_rate_limits"
DEFAULT_RATE_LIMIT = 5
RATE_LIMIT_WINDOW_SECONDS = 60 * 60
TURNSTILE_VERIFY_URL = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)
ALLOWED_TOPICS = {"job", "collaboration", "feedback", "other"}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class WebsiteMessageValidationError(ValueError):
    """留言內容或人機驗證無效。"""


class WebsiteMessageRateLimitExceeded(RuntimeError):
    """同一訪客在目前時段送出過多留言。"""


class WebsiteMessageServiceUnavailable(RuntimeError):
    """外部驗證或資料儲存服務暫時無法使用。"""


@dataclass(frozen=True)
class WebsiteMessage:
    name: str
    email: str
    topic: str
    message: str
    turnstile_token: str
    is_honeypot: bool = False


def parse_allowed_hostnames(
    value: str | None,
    cors_origins: list[str] | None = None,
) -> set[str]:
    """解析 Turnstile hostname；未指定時沿用 CORS origins。"""

    if value and value.strip():
        return {
            hostname.strip().lower()
            for hostname in value.split(",")
            if hostname.strip()
        }

    hostnames: set[str] = set()
    for origin in cors_origins or []:
        hostname = urlsplit(origin).hostname
        if hostname:
            hostnames.add(hostname.lower())
    return hostnames


def validate_message_payload(data: object) -> WebsiteMessage:
    if not isinstance(data, dict):
        raise WebsiteMessageValidationError(
            "請使用 JSON 格式傳送留言。"
        )

    def clean_string(field: str) -> str:
        value = data.get(field, "")
        if not isinstance(value, str):
            raise WebsiteMessageValidationError("留言格式不正確。")
        return value.strip()

    name = clean_string("name")
    email = clean_string("email").lower()
    topic = clean_string("topic")
    message = clean_string("message")
    website = clean_string("website")
    turnstile_token = clean_string("turnstile_token")

    # 這個欄位正常使用者看不到。機器人填入時回傳成功，但不寫入資料。
    if website:
        return WebsiteMessage(
            name="",
            email="",
            topic="other",
            message="",
            turnstile_token="",
            is_honeypot=True,
        )

    if not name or len(name) > 80:
        raise WebsiteMessageValidationError("姓名需為 1 到 80 個字。")
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        raise WebsiteMessageValidationError("請輸入有效的 Email。")
    if topic not in ALLOWED_TOPICS:
        raise WebsiteMessageValidationError("請選擇有效的留言主題。")
    if len(message) < 10 or len(message) > 2000:
        raise WebsiteMessageValidationError(
            "留言內容需為 10 到 2000 個字。"
        )
    if not turnstile_token or len(turnstile_token) > 2048:
        raise WebsiteMessageValidationError("請完成人機驗證。")

    return WebsiteMessage(
        name=name,
        email=email,
        topic=topic,
        message=message,
        turnstile_token=turnstile_token,
    )


class TurnstileVerifier:
    def __init__(
        self,
        secret_key: str,
        allowed_hostnames: set[str],
        *,
        timeout_seconds: float = 5,
    ) -> None:
        if not secret_key:
            raise WebsiteMessageServiceUnavailable(
                "缺少 TURNSTILE_SECRET_KEY"
            )
        self.secret_key = secret_key
        self.allowed_hostnames = allowed_hostnames
        self.timeout_seconds = timeout_seconds

    def verify(self, token: str, remote_ip: str) -> None:
        try:
            response = requests.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": self.secret_key,
                    "response": token,
                    "remoteip": remote_ip,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as error:
            raise WebsiteMessageServiceUnavailable(
                "Turnstile 驗證服務暫時無法使用"
            ) from error

        if not isinstance(result, dict) or result.get("success") is not True:
            raise WebsiteMessageValidationError(
                "人機驗證未通過，請重新驗證後再送出。"
            )

        hostname = str(result.get("hostname") or "").lower()
        if self.allowed_hostnames and hostname not in self.allowed_hostnames:
            raise WebsiteMessageValidationError(
                "人機驗證來源不正確，請重新整理頁面。"
            )

        if result.get("action") != "contact":
            raise WebsiteMessageValidationError(
                "人機驗證用途不正確，請重新整理頁面。"
            )


class WebsiteMessageRepository:
    def __init__(self) -> None:
        load_dotenv()

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise WebsiteMessageServiceUnavailable(
                "缺少 GOOGLE_CLOUD_PROJECT"
            )

        try:
            rate_limit = int(
                os.getenv(
                    "WEBSITE_MESSAGE_RATE_LIMIT",
                    str(DEFAULT_RATE_LIMIT),
                )
            )
        except ValueError as error:
            raise WebsiteMessageServiceUnavailable(
                "WEBSITE_MESSAGE_RATE_LIMIT 必須是整數"
            ) from error

        if rate_limit < 1:
            raise WebsiteMessageServiceUnavailable(
                "WEBSITE_MESSAGE_RATE_LIMIT 必須大於 0"
            )

        self.client = firestore.Client(project=project_id)
        self.messages = self.client.collection(
            os.getenv(
                "FIRESTORE_WEBSITE_MESSAGE_COLLECTION",
                DEFAULT_MESSAGE_COLLECTION,
            )
        )
        self.rate_limits = self.client.collection(
            os.getenv(
                "FIRESTORE_MESSAGE_RATE_LIMIT_COLLECTION",
                DEFAULT_RATE_LIMIT_COLLECTION,
            )
        )
        self.rate_limit = rate_limit

    def create(self, message: WebsiteMessage, visitor_hash: str) -> str:
        now = datetime.now(timezone.utc)
        window_number = int(now.timestamp()) // RATE_LIMIT_WINDOW_SECONDS
        rate_document_id = hashlib.sha256(
            f"{visitor_hash}:{window_number}".encode("utf-8")
        ).hexdigest()
        rate_reference = self.rate_limits.document(rate_document_id)

        @firestore.transactional
        def reserve_rate_limit(transaction) -> None:
            snapshot = rate_reference.get(transaction=transaction)
            stored = snapshot.to_dict() if snapshot.exists else {}
            count = int((stored or {}).get("count", 0))
            if count >= self.rate_limit:
                raise WebsiteMessageRateLimitExceeded

            transaction.set(
                rate_reference,
                {
                    "count": count + 1,
                    "window_number": window_number,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )

        reserve_rate_limit(self.client.transaction())

        document_reference = self.messages.document()
        document_reference.set({
            "name": message.name,
            "email": message.email,
            "topic": message.topic,
            "message": message.message,
            "status": "new",
            "channel": "website",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        return document_reference.id


class WebsiteMessageService:
    def __init__(
        self,
        *,
        cors_origins: list[str],
        repository: WebsiteMessageRepository | None = None,
        verifier: TurnstileVerifier | None = None,
    ) -> None:
        secret_key = os.getenv("TURNSTILE_SECRET_KEY", "").strip()
        allowed_hostnames = parse_allowed_hostnames(
            os.getenv("TURNSTILE_ALLOWED_HOSTNAMES"),
            cors_origins,
        )
        self.repository = repository or WebsiteMessageRepository()
        self.verifier = verifier or TurnstileVerifier(
            secret_key,
            allowed_hostnames,
        )
        self.secret_key = secret_key

    def submit(self, data: object, remote_ip: str) -> str | None:
        message = validate_message_payload(data)
        if message.is_honeypot:
            return None

        self.verifier.verify(message.turnstile_token, remote_ip)
        visitor_hash = hmac.new(
            self.secret_key.encode("utf-8"),
            remote_ip.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return self.repository.create(message, visitor_hash)


@lru_cache(maxsize=1)
def get_website_message_service(
    cors_origins: tuple[str, ...],
) -> WebsiteMessageService:
    return WebsiteMessageService(cors_origins=list(cors_origins))
