import os
from functools import lru_cache
from flask_cors import CORS

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from career_bot_service import CareerBotService
from website_message_service import (
    WebsiteMessageRateLimitExceeded,
    WebsiteMessageServiceUnavailable,
    WebsiteMessageValidationError,
    get_website_message_service,
)

load_dotenv()

line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not line_channel_secret:
    raise ValueError("缺少 LINE_CHANNEL_SECRET 環境變數")

if not line_channel_access_token:
    raise ValueError("缺少 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

app = Flask(__name__)


def parse_cors_allowed_origins(value: str | None) -> list[str]:
    """解析逗號分隔的前端 origin，並拒絕不安全的萬用字元。"""

    origins = [
        origin.strip().rstrip("/")
        for origin in (value or "").split(",")
        if origin.strip()
    ]
    if "*" in origins:
        raise ValueError(
            "CORS_ALLOWED_ORIGINS 不可使用 *，請明確列出允許的網站 origin"
        )
    return list(dict.fromkeys(origins))


cors_allowed_origins = parse_cors_allowed_origins(
    os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4321",
    )
)

CORS(
    app,
    resources={
        r"/api/chat": {
            "origins": cors_allowed_origins,
            "methods": ["POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        },
        r"/api/messages": {
            "origins": cors_allowed_origins,
            "methods": ["POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        },
    },
)

line_configuration = Configuration(
    access_token=line_channel_access_token
)

line_handler = WebhookHandler(
    line_channel_secret
)


@lru_cache(maxsize=1)
def get_career_bot_service() -> CareerBotService:
    """首次收到文字訊息時才初始化雲端服務與 RAG 索引。"""

    return CareerBotService()


def get_line_display_name(
    messaging_api: MessagingApi,
    line_user_id: str | None,
) -> str | None:
    """取得 LINE 顯示名稱；查詢失敗時不阻斷訊息處理。"""

    if not line_user_id:
        return None

    try:
        profile = messaging_api.get_profile(line_user_id)
    except Exception:
        app.logger.warning("無法取得 LINE 使用者 Profile", exc_info=True)
        return None

    display_name = getattr(profile, "display_name", None)
    if not isinstance(display_name, str):
        return None

    return display_name.strip() or None


@app.get("/")
def index():
    return "LINE Career Bot is running!"


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "請使用 JSON 格式傳送問題。"
        }), 400

    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "請輸入想詢問的問題。"
        }), 400

    question = question.strip()

    if len(question) > 500:
        return jsonify({
            "error": "問題不可超過 500 個字。"
        }), 400

    try:
        result = get_career_bot_service().handle_message(
            question=question,
            line_user_id=None,
            display_name=None,
            channel="website",
        )
    except Exception:
        app.logger.exception("處理網站 AI 問答時發生錯誤")
        return jsonify({
            "error": "AI 服務暫時無法使用，請稍後再試。"
        }), 503

    app.logger.info(
        "網站問答分流完成：route=%s source_ids=%s",
        result.route.value,
        result.source_ids,
    )

    return jsonify({
        "route": result.route.value,
        "response": result.response,
        "source_ids": result.source_ids,
    })


def get_client_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    forwarded_ips = [
        value.strip()
        for value in forwarded_for.split(",")
        if value.strip()
    ]
    # Google Front End 會在尾端加入 client IP 與 proxy IP；忽略前方可偽造值。
    forwarded_ip = (
        forwarded_ips[-2]
        if len(forwarded_ips) >= 2
        else (forwarded_ips[0] if forwarded_ips else "")
    )
    return forwarded_ip or request.remote_addr or "unknown"


@app.route("/api/messages", methods=["POST", "OPTIONS"])
def create_website_message():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)
    try:
        document_id = get_website_message_service(
            tuple(cors_allowed_origins)
        ).submit(data, get_client_ip())
    except WebsiteMessageValidationError as error:
        return jsonify({"error": str(error)}), 400
    except WebsiteMessageRateLimitExceeded:
        response = jsonify({
            "error": "留言次數較多，請稍後再試。"
        })
        response.headers["Retry-After"] = "3600"
        return response, 429
    except WebsiteMessageServiceUnavailable:
        app.logger.exception("私人留言服務設定或外部服務發生錯誤")
        return jsonify({
            "error": "留言服務暫時無法使用，請稍後再試。"
        }), 503
    except Exception:
        app.logger.exception("儲存網站私人留言時發生錯誤")
        return jsonify({
            "error": "留言服務暫時無法使用，請稍後再試。"
        }), 503

    if document_id:
        app.logger.info("網站私人留言已建立：document_id=%s", document_id)

    return jsonify({
        "message": "留言已送出，謝謝你！"
    }), 201


@app.post("/callback")
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    if not signature:
        abort(400)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@line_handler.add(
    MessageEvent,
    message=TextMessageContent,
)
def handle_text_message(event):
    user_message = event.message.text.strip()

    with ApiClient(line_configuration) as api_client:
        messaging_api = MessagingApi(api_client)

        if not user_message:
            reply_text = "請輸入你想詢問的問題。"
        else:
            try:
                event_source = getattr(event, "source", None)
                line_user_id = getattr(event_source, "user_id", None)
                display_name = get_line_display_name(
                    messaging_api,
                    line_user_id,
                )
                result = get_career_bot_service().handle_message(
                    question=user_message,
                    line_user_id=line_user_id,
                    display_name=display_name,
                )
                reply_text = result.response
                app.logger.info(
                    "求職問答分流完成：route=%s source_ids=%s unknown_question_id=%s",
                    result.route.value,
                    result.source_ids,
                    result.unknown_question_id,
                )
            except Exception:
                app.logger.exception("處理求職問答時發生錯誤")
                reply_text = "抱歉，AI 服務暫時無法使用，請稍後再試。"

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=reply_text)
                ],
            )
        )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        debug=False,
    )
