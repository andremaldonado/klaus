import os
import requests
from typing import Any, Dict
from externals.habitica_api import get_tasks
from ai_assistant import generate_tasks_suggestion

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

allowed_ids_str = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS")
if allowed_ids_str is None:
    raise EnvironmentError("Environment variable TELEGRAM_ALLOWED_CHAT_IDS is not set.")

ALLOWED_CHAT_IDS = {
    int(chat_id.strip())
    for chat_id in allowed_ids_str.split(",") if chat_id.strip()
}


def validate_telegram_request(request: Any) -> Dict[str, Any]:
    """
    Validates the Telegram request.

    Returns a dictionary containing:
      - valid: (bool) whether the request is valid.
      - status_code: (int) appropriate HTTP status code.
      - message: (str) error message if invalid.
      - chat_id: (int) chat ID if valid.
      - text: (str) user's message text, if provided.
    """
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header_secret != TELEGRAM_SECRET_TOKEN:
        return {"valid": False, "status_code": 403, "message": "Forbidden: Invalid token."}

    body = request.get_json(silent=True)
    if not body or "message" not in body:
        return {"valid": False, "status_code": 400, "message": "Bad Request: Missing message data."}

    message = body.get("message")
    if not message:
        return {"valid": False, "status_code": 400, "message": "Bad Request: Message not provided."}

    chat = message.get("chat")
    if not chat or not chat.get("id"):
        return {"valid": False, "status_code": 400, "message": "Bad Request: Invalid chat data."}

    chat_id = chat["id"]
    if chat_id not in ALLOWED_CHAT_IDS:
        send_telegram_message(chat_id, "Access denied. Private bot.")
        return {"valid": False, "status_code": 403, "message": "Forbidden: Unauthorized chat."}

    text = message.get("text", "What are my tasks?")
    return {"valid": True, "status_code": 200, "chat_id": chat_id, "text": text}


def send_telegram_message(chat_id: int, text: str) -> None:
    """
    Sends a message to the specified Telegram chat.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
