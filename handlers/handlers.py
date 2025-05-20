import pytz
import os
from ai_assistant import generate_tasks_suggestion, chat
from datetime import datetime, timedelta, timezone
from data.memory import save_message, save_embedding, fetch_similar_memories
from externals.habitica_api import get_tasks, find_task_by_message, create_task_todo, complete_task
from externals.calendar_api import list_today_events, create_event


# Constants
PRIORITY_MAP = {"low": 0.1, "medium": 1, "high": 2}
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# Common functions
def _parse_iso_date(date_text: str) -> str | None:
    """
    Converts Portuguese date keywords into an ISO-8601 string.
    Supports 'hoje' and 'amanhã'.
    """
    if not date_text:
        return None
    now = datetime.now(TIMEZONE)
    key = date_text.strip().lower()
    if key == "hoje":
        return now.isoformat() + "Z"
    if key == "amanhã":
        return (now + timedelta(days=1)).isoformat() + "Z"
    return None


def _save_message(bot_role: bool, text: str, chat_id: str) -> str:
    # Save message and embedding to the database
    if bot_role: chat_id = f"assistant_{chat_id}"
    message_id, saved_data = save_message(chat_id, text)
    save_embedding(text, chat_id, message_id)


# Task handlers
def handle_task_status(chat_id: str, user_message: str, start_date: str) -> str:
    _save_message(False, user_message, chat_id)
    tasks = get_tasks(_parse_iso_date(start_date) == "hoje")
    events = list_today_events(chat_id)
    tasks_suggestion = generate_tasks_suggestion(tasks, events, user_message)
    _save_message(True, tasks_suggestion, chat_id)
    return tasks_suggestion


def handle_new_task(chat_id: str, user_message: str, title: str, priority: str, start_date: str) -> str:
    title = title or user_message
    _save_message(False, user_message, chat_id)
    priority = PRIORITY_MAP.get(priority, 1)
    iso_date = _parse_iso_date(start_date)
    create_task_todo(title, notes="", priority=priority, iso_date=iso_date)
    response = f"✅ Tarefa \"{title}\" criada! Vamos em frente!"
    _save_message(True, response, chat_id)
    return response


def handle_task_conclusion(chat_id: str, user_message: str, title: str) -> str:
    _save_message(False, user_message, chat_id)
    tasks = get_tasks()
    match = find_task_by_message(tasks, title)
    complete_task(match["id"])
    response = f"✅ Tarefa \"{match['title']}\" concluída! Bom trabalho!"
    _save_message(True, response, chat_id)
    return response


def handle_list_calendar(chat_id: str, user_message: str) -> str:
    _save_message(False, user_message, chat_id)
    try:
        events = list_today_events(chat_id)
        response = "Eventos de hoje:\n" + "\n".join(events)
    except Exception as e:
        response = "Parece que houve um erro ao acessar sua agenda. Para autorizar, digite \"Autorizar agenda\". Erro 001."
    _save_message(True, response, chat_id)
    return response


def handle_create_calendar(chat_id: str, user_message: str, title: str, start: str, end: str) -> str:
    _save_message(False, user_message, chat_id)
    try:
        create_event(chat_id, title, start, end)
        response = f"Evento '{title}' criado na sua agenda."
    except Exception as e:
        response = "Parece que houve um erro ao acessar sua agenda. Para autorizar, digite \"Autorizar agenda\". Erro 003."
    _save_message(True, response, chat_id)
    return response


# General handlers
def handle_general_chat(chat_id: str, user_message: str) -> str:
    _save_message(False, user_message, chat_id)
    # Fetch context for the chat
    relevant_memories = fetch_similar_memories(chat_id, user_message, 15)
    memory_block = "\n".join(relevant_memories)
    response = chat(user_message, memory_block)
    _save_message(True, response, chat_id)
    return response
