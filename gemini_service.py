import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")


if not project_id:
    raise ValueError("缺少 GOOGLE_CLOUD_PROJECT 環境變數")  

if not location:
    raise ValueError("缺少 GOOGLE_CLOUD_LOCATION 環境變數")

client = genai.Client(
    vertexai=True,
    project=project_id,
    location=location
)


def ask_gemini(user_message: str) -> str:
    chat = client.chats.create(
        model="gemini-3.7-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "你是一個親切且回答清楚的LINE 聊天機器人。"
                "請使用繁體中文回答，並讓內容適合在手機中閱讀。"
            ),
            max_output_tokens=1000,
        ),
    )

    response = chat.send_message(user_message)

    if not response.text:
        raise ValueError("抱歉，我目前無法回答這個問題。請稍後再試。")

    return response.text[:4500]