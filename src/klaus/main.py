import base64
import os
import functions_framework
import pytz
import logging

from handlers.ai_assistant import interpret_user_message
from auth.auth_handler import handle_google_auth, authenticate_request
from datetime import datetime
from handlers.general import handle_general_chat
from handlers.calendar import handle_list_calendar, handle_create_calendar
from handlers.task import handle_task_status, handle_new_task, handle_task_conclusion
from handlers.list import handle_create_list_item, handle_list_user_list_items, handle_remove_list_item

from pydantic import ValidationError
from schemas import ChatRequest


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def webhook(request):

    logger.debug(f"▶️ [BASICS] Request Method: {request.method}")
    logger.debug(f"▶️ [BASICS] Request Path: {request.path}")
    logger.debug(f"▶️ [BASICS] Request Headers: {request.headers}")

    # CORS preflight
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": os.getenv("CORS_ALLOW_ORIGIN", "http://localhost:8081"),
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
        return ('', 204, headers)

    # OAuth2 Google authorization
    if request.path.endswith("/auth/google") and request.method == "POST":
        return handle_google_auth(request)

    # For all other requests
    headers = {
        "Access-Control-Allow-Origin": os.getenv("CORS_ALLOW_ORIGIN", "http://localhost:8081"),
        "Access-Control-Allow-Credentials": "true"
    }

    chat_id = None
    response_code, chat_id = authenticate_request(request.headers.get("Authorization", ""))
    logger.debug(f"▶️ [DEBUG] chat_id = {chat_id}")
    if chat_id is None  or response_code != 200:
        return "Unauthorized user", response_code, headers

    body = ""
    try:
        body = ChatRequest(**(request.get_json(silent=True) or {}))
    except ValidationError as err:
        logger.error(f"❌ [ERROR] Bad request: {err}")
        return f"Bad Request: {err}", 400, headers

    try:
        user_message = body.text
        logger.debug(f"▶️ [DEBUG] user_message = {user_message}")
        if not user_message:
            logger.error(f"❌ [ERROR] Bad request: {err}")
            return "Bad Request: No text provided", 400, headers

        # Interpret intent
        message = interpret_user_message(user_message)
        intent = message.get("type")

        # Dispatch based on intent
        if intent == "list_calendar":
            response = handle_list_calendar(chat_id, user_message)
        elif intent == "create_calendar":
            response = handle_create_calendar(chat_id, user_message, message.get("title"), message.get("start_date"), message.get("end_date"))
        elif intent == "task_status":
            response = handle_task_status(chat_id, user_message, message.get("start_date"))
        elif intent == "new_task":
            response = handle_new_task(chat_id, user_message, message.get("title"), message.get("priority"), message.get("start_date"))
        elif intent == "task_conclusion":
            response = handle_task_conclusion(chat_id, user_message, message.get("title"))
        elif intent == "create_list_item":
            response = handle_create_list_item(chat_id, user_message, message.get("title"), message.get("items"))
        elif intent == 'remove_list_item':
            response = handle_remove_list_item(chat_id, user_message, message.get("title"), message.get("items"))
        elif intent == "list_user_list_items":
            response = handle_list_user_list_items(chat_id, user_message, message.get("title"))
        else:
            response = handle_general_chat(chat_id, user_message)

        response = {"response": response, "intent": intent, "date": datetime.now(TIMEZONE).isoformat()}
        logger.debug(f"▶️ [BASICS] {response}")
        return response, 200, headers

    except Exception as e:
        code = 500
        logger.error(f"❌ [ERROR] General exception: {e}")
        return f"Error: {e}", code, headers
