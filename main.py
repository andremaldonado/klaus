import functions_framework
from ai_assistant import interpret_user_message
from datetime import datetime, timedelta, timezone
from handlers.telegram_handler import validate_telegram_request, send_telegram_message
from handlers.handlers import handle_task_status, handle_new_task, handle_task_conclusion, handle_general_chat, handle_calendar_auth, handle_calendar_code, handle_list_calendar, handle_create_calendar


@functions_framework.http
def webhook(request):
    source = request.args.get("source", "telegram").lower()

    # Validate Telegram source
    chat_id = None
    if source == "telegram":
        validation = validate_telegram_request(request)
        if not validation["valid"]:
            return validation["message"], validation["status_code"]
        chat_id = validation["chat_id"]

    if chat_id is None:
        chat_id = request.args.get("chat_id", "user1")

    try:
        body = request.get_json(silent=True) or {}
        # Extract user text from either {"message": {"text": ...}} or {"text": ...}
        user_message = (
            body.get("message", {}).get("text")
            or body.get("text")
            or ""
        )
        if not user_message:
            return "No text provided", 400

        # Interpret intent
        message = interpret_user_message(user_message)
        intent = message.get("type")

        # Dispatch based on intent
        if intent == "calendar_auth":
            response = handle_calendar_auth(chat_id)
        elif intent == "calendar_code":
            response = handle_calendar_code(chat_id, message.get("details"))
        elif intent == "list_calendar":
            response = handle_list_calendar(chat_id)
        elif intent == "create_calendar":
            response = handle_create_calendar(chat_id, message.get("title"), message.get("start_date"), message.get("end_date"))
        elif intent == "task_status":
            response = handle_task_status(chat_id, message.get("start_date"), user_message)
        elif intent == "new_task":
            response = handle_new_task(message.get("title"), message.get("priority"), message.get("start_date"), user_message)
        elif intent == "task_conclusion":
            response = handle_task_conclusion(message.get("title"))
        else:
            response = handle_general_chat(chat_id, user_message)

        # Return or send via Telegram
        if source == "telegram":
            send_telegram_message(chat_id, response)
            return "Message sent via Telegram.", 200

        return response, 200

    except Exception as e:
        code = 500
        if source == "telegram":
            # For Telegram, we catch and return 200 so Telegram doesn't retry
            send_telegram_message(chat_id, f"Estou passando por dificuldades. Tente novamente mais tarde. Erro: {e}")
            code = 200
        return f"Error: {e}", code
