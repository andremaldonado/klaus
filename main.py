import base64
import os
import functions_framework
import pytz
import logging

from ai_assistant import interpret_user_message
from auth.auth_handler import handle_google_auth, get_id_info
from auth.utils import refresh_id_token, extract_email_from_token
from datetime import datetime, timezone
from handlers.handlers import handle_task_status, handle_new_task, handle_task_conclusion, handle_general_chat, handle_list_calendar, handle_create_calendar

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import ValidationError
from schemas import ChatRequest


TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def _sanitize_id(raw: str) -> str:
    token = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    return token.rstrip("=")


@functions_framework.http
def webhook(request):

    logger.debug(f"▶️ [DEBUG] request = {request}")

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

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return "Missing or invalid Authorization header", 401, headers

    id_token_str = auth_header.split(" ", 1)[1]
    try:
        idinfo = get_id_info(id_token_str)
    except Exception as e:
        logger.warning(f"⚠️ Invalid Token: {e} — trying auto-refresh")
        try:
            email_guess = extract_email_from_token(id_token_str)
            chat_id = _sanitize_id(email_guess)
            id_token_str = refresh_id_token(chat_id)
            idinfo = get_id_info(id_token_str)
        except Exception as refresh_error:
            logger.error(f"❌ Refresh token has failed: {refresh_error}")
            return f"Invalid ID token and refresh failed: {refresh_error}", 401, headers

    email = idinfo.get("email")
    if not idinfo.get("email_verified"):
        return "Email not verified", 403, headers

    allowed = os.getenv("ALLOWED_EMAILS", "").split(",")
    if email not in allowed:
        return "Unauthorized user", 403, headers

    chat_id = _sanitize_id(email)
    logger.debug(f"▶️ [DEBUG] chat_id = {chat_id}")

    if chat_id is None:
        return "Unauthorized user - no chat ID", 403, headers

    body = ""
    try:
        body = ChatRequest(**(request.get_json(silent=True) or {}))
    except ValidationError as err:
        logger.error(f"❌ [ERROR] Bad request: {err}")
        return f"Bad Request: {err}", 400, headers

    try:
        user_message = body.text
        if not user_message:
            logger.error(f"❌ [ERROR] Bad request: {err}")
            return "Bad Request: No text provided", 400, headers

        # Interpret intent
        message = interpret_user_message(user_message)
        logger.debug(f"▶️ [DEBUG] message = {message}")
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
        else:
            response = handle_general_chat(chat_id, user_message)

        response = {"response": response, "intent": intent, "date": datetime.now(TIMEZONE).isoformat()}
        return response, 200, headers

    except Exception as e:
        code = 500
        return f"Error: {e}", code, headers
