from handlers.ai_assistant import generate_tasks_suggestion
from handlers.utils import parse_iso_date, save_message_embedding
from externals.habitica_api import get_tasks, find_task_by_message, create_task_todo, complete_task
from externals.calendar_api import list_today_events
from schemas import User


# Constants
PRIORITY_MAP = {"low": 0.1, "medium": 1, "high": 2}


def handle_task_status(user: User, user_message: str, start_date: str) -> str:
    save_message_embedding(False, user_message, user.chat_id)
    tasks = get_tasks(user.habitica_id, user.habitica_token, parse_iso_date(start_date) == "hoje")
    events = list_today_events(user.chat_id)
    tasks_suggestion = generate_tasks_suggestion(tasks, events, user_message)
    save_message_embedding(True, tasks_suggestion, user.chat_id)
    return tasks_suggestion


def handle_new_task(user: User, user_message: str, title: str, priority: str, start_date: str) -> str:
    if not title:
        response = "Parece que você não especificou o título da tarefa. Lembre-se de colocar o título da tarefa entre \"aspas\"."
        return response

    save_message_embedding(False, user_message, user.chat_id)
    priority = PRIORITY_MAP.get(priority, 1)
    iso_date = parse_iso_date(start_date)
    create_task_todo(user.habitica_id, user.habitica_token, title, notes="", priority=priority, iso_date=iso_date)
    response = f"✅ Tarefa \"{title}\" criada! Vamos em frente!"
    save_message_embedding(True, response, user.chat_id)
    return response


def handle_task_conclusion(user: User, user_message: str, title: str) -> str:
    if not title:
        response = "Parece que você não especificou o título da tarefa. Lembre-se de colocar o título da tarefa entre \"aspas\"."
        return response
    
    save_message_embedding(False, user_message, user.chat_id)
    match = find_task_by_message(user.habitica_id, user.habitica_token, title)
    complete_task(user.habitica_id, user.habitica_token, match["id"])
    response = f"✅ Tarefa \"{match['title']}\" concluída! Bom trabalho!"
    save_message_embedding(True, response, user.chat_id)
    return response