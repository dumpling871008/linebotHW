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

load_dotenv()

line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not line_channel_secret:
    raise ValueError("缺少 LINE_CHANNEL_SECRET 環境變數")

if not line_channel_access_token:
    raise ValueError("缺少 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

app = Flask(__name__)

cors_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4321",
    ).split(",")
    if origin.strip()
]

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": cors_allowed_origins,
        }
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


@app.post("/api/chat")
def chat():
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
