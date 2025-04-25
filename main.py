import functions_framework
from datetime import datetime, timedelta
from data.memory import save_message, get_latest_messages
from externals.habitica_api import get_tasks, find_task_by_message, create_task_todo, complete_task
from ai_assistant import generate_tasks_suggestion, interpret_user_message, chat
from handlers.telegram_handler import validate_telegram_request, send_telegram_message

# Constants
PRIORITY_MAP = {"low": 0.1, "medium": 1, "high": 2}


def _parse_iso_date(date_text: str) -> str | None:
    """
    Converts Portuguese date keywords into an ISO-8601 string.
    Supports 'hoje' and 'amanhã'.
    """
    if not date_text:
        return None
    now = datetime.now()
    key = date_text.strip().lower()
    if key == "hoje":
        return now.isoformat() + "Z"
    if key == "amanhã":
        return (now + timedelta(days=1)).isoformat() + "Z"
    return None


def _handle_task_status(user_message: str) -> str:
    tasks = get_tasks()
    return generate_tasks_suggestion(tasks, user_message)


def _handle_new_task(interpretation: dict, user_message: str) -> str:
    title = interpretation.get("task") or user_message
    priority = PRIORITY_MAP.get(interpretation.get("priority"), 1)
    iso_date = _parse_iso_date(interpretation.get("date"))
    create_task_todo(title, notes="", priority=priority, iso_date=iso_date)
    return "Tarefa criada! Vamos em frente!"


def _handle_task_conclusion(interpretation: dict) -> str:
    title = interpretation.get("task")
    tasks = get_tasks()
    match = find_task_by_message(tasks, title)
    complete_task(match["id"])
    return f"Tarefa \"{match['title']}\" concluída! Bom trabalho!"


@functions_framework.http
def webhook(request):
    source = request.args.get("source", "telegram").lower()

    # Validate Telegram source
    telegram_chat_id = None
    if source == "telegram":
        validation = validate_telegram_request(request)
        if not validation["valid"]:
            return validation["message"], validation["status_code"]
        telegram_chat_id = validation["chat_id"]

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
        
        # Save user message to the database
        save_message("user", user_message)

        # Interpret intent
        intent = interpret_user_message(user_message)["type"]

        # Dispatch based on intent
        if intent == "task_status":
            response = _handle_task_status(user_message)
        elif intent == "new_task":
            interp = interpret_user_message(user_message)
            response = _handle_new_task(interp, user_message)
        elif intent == "task_conclusion":
            interp = interpret_user_message(user_message)
            response = _handle_task_conclusion(interp)
        else:
            context = get_latest_messages()
            context = [msg["text"] for msg in context]
            response = chat(user_message, context)

        # Save assistant response to the database
        save_message("assistant", response)

        # Return or send via Telegram
        if source == "telegram":
            send_telegram_message(telegram_chat_id, response)
            return "Message sent via Telegram.", 200

        return response, 200

    except Exception as e:
        # For Telegram, we catch and return 200 so Telegram doesn't retry
        code = 200 if source == "telegram" else 500
        return f"Error: {e}", code
