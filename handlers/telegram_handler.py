import os
import requests
from habitica_api import get_tasks
from ai_assistant import generate_chatgpt_suggestion

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

ALLOWED_CHAT_IDS = {
    int(chat_id.strip())
    for chat_id in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS").split(",")
}

def handle_telegram_request(request):
    """
    Processes the Telegram request.
    Validates the token and authorized chat, fetches tasks, generates a response,
    and sends a message back to the user.
    """
    validation = validate_telegram_request(request)
    if not validation.get("valid"):
        return validation.get("message"), validation.get("status_code")

    chat_id = validation["chat_id"]
    user_context = validation.get("text", "What are my tasks?")

    try:
        tasks = get_tasks()
        response = generate_chatgpt_suggestion(tasks, user_context)
        send_message_telegram(chat_id, response)
        return "OK", 200
    except Exception as e:
        error_message = f"Internal Error: {str(e)}"
        send_message_telegram(chat_id, error_message)
        status_code = getattr(e, "status_code", 500)
        return error_message, status_code

def validate_telegram_request(request):
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
    if not body:
        return {"valid": False, "status_code": 400, "message": "Bad Request: Empty or invalid body."}

    message = body.get("message")
    if not message:
        return {"valid": False, "status_code": 400, "message": "Bad Request: No message found."}

    chat = message.get("chat")
    if not chat or not chat.get("id"):
        return {"valid": False, "status_code": 400, "message": "Bad Request: Invalid chat data."}

    chat_id = chat["id"]
    if chat_id not in ALLOWED_CHAT_IDS:
        send_message_telegram(chat_id, "Access denied. Private bot.")
        return {"valid": False, "status_code": 403, "message": "Forbidden: Unauthorized chat."}

    text = message.get("text", "What are my tasks?")
    return {"valid": True, "status_code": 200, "chat_id": chat_id, "text": text}

def send_message_telegram(chat_id, text):
    """
    Sends a message to the specified Telegram chat.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
