import os
import base64
import pytz
import logging
import time

from datetime import datetime
from flask import Flask, request, jsonify, make_response, Response
from handlers.ai_assistant import interpret_user_message
from auth.auth_handler import handle_google_auth, authenticate_request
from handlers.general import handle_general_chat, handle_get_message
from handlers.calendar import handle_list_calendar, handle_create_calendar
from handlers.task import handle_task_status, handle_new_task, handle_task_conclusion
from handlers.list import handle_create_list_item, handle_list_user_list_items, handle_remove_list_item
from pydantic import ValidationError
from schemas import ChatRequest

# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# Logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def create_app(*args, **kwargs):
    app = Flask(__name__)


    # 🔥 CORS Middleware
    @app.after_request
    def apply_cors(response):
        response.headers['Access-Control-Allow-Origin'] = os.getenv("CORS_ALLOW_ORIGIN", "http://localhost:8081")
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response


    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            return make_response('', 204)


    @app.route('/auth/google', methods=['POST'])
    def google_auth():
        return handle_google_auth(request)


    @app.route('/check-message')
    def check_message():
        auth_header = request.headers.get("Authorization", "")
        response_code, chat_id = authenticate_request(auth_header)
        if chat_id is None or response_code != 200:
            return make_response("Unauthorized user", response_code)
            
        message = handle_get_message(chat_id)
        if message:
            logger.debug(f"▶️ {datetime.now(TIMEZONE).strftime('%H:%M:%S')} - Found pending message: ({message['id']}) {message['text']})")
            payload = {
                "response": message["text"],
                "intent": "agent_message",
                "date": message["created_at"]
            }
            return jsonify(payload), 200
        
        return make_response("No pending messages", 204)

  
    @app.route('/', methods=['POST'])
    def webhook():
        logger.debug(f"▶️ {datetime.now(TIMEZONE).strftime('%H:%M:%S')} - webhook() -> {request.path}")
        
        auth_header = request.headers.get("Authorization", "")
        response_code, chat_id = authenticate_request(auth_header)
        if chat_id is None or response_code != 200:
            return make_response("Unauthorized user", response_code)

        try:
            json_data = request.get_json(silent=True) or {}
            body = ChatRequest(**json_data)
        except ValidationError as err:
            logger.error(f"❌ [ERROR] Bad request: {err}")
            return make_response(f"Bad Request: {err}", 400)

        try:
            user_message = body.text
            if not user_message:
                return make_response("Bad Request: No text provided", 400)

            message = interpret_user_message(user_message)
            intent = message.get("type")

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

            payload = {
                "response": response,
                "intent": intent,
                "date": datetime.now(TIMEZONE).isoformat()
            }
            return jsonify(payload), 200

        except Exception as e:
            logger.error(f"❌ [ERROR] General exception: {e}")
            return make_response(f"Error: {e}", 500)

    return app


app = create_app()

if __name__ == "__main__":
    print(" Starting Klaus...")
    app.run(debug=(_ENVIRONMENT == "dev"))
