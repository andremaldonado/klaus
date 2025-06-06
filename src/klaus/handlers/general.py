import pytz
import os
import logging

from handlers.ai_assistant import chat, check_intents
from data.memory import fetch_similar_memories, get_latest_messages
from handlers.utils import save_message_embedding
from externals.habitica_api import get_tasks
from externals.calendar_api import list_today_events

# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


# General handler
def handle_general_chat(chat_id: str, user_message: str) -> str:
    # 1) Fetch context of similar memories
    messages = []
    relevant_memories = fetch_similar_memories(chat_id, user_message, 15)
    if relevant_memories:
        messages.append({
            "role": "system",
            "content": "Memórias relevantes similares ao assunto tratado:" + "\n - ".join(relevant_memories)
        })

    # 2) Fetch latest messages
    history = get_latest_messages(chat_id, 10) 
    if history:
        messages.append({
            "role": "system",
            "content": "Histórico recente de mensagens trocadas:"
        })
        for msg in history:
            role = msg["role"]
            if role == "klaus":
                role = "system" # retrocompatibility only
            messages.append({"role": role, "content": msg["text"]})

    # 3) User message
    save_message_embedding(False, user_message, chat_id)

    # 4) Check for calendar and task intents to include in the context
    intents = check_intents(user_message)
    if "calendar" in intents:
        events = list_today_events(chat_id)
        if events:
            messages.append({
                "role": "system",
                "content": f"Eventos do usuário em sua agenda, caso seja útil:\n {events}"
            })
    if "tasks" in intents:
        tasks = get_tasks()
        if tasks:
            messages.append({
                "role": "system",
                "content": f"Tarefas do usuário em sua lista de tarefas, caso seja útil:\n {tasks}"
            })

    # 5) Generate response
    response = chat(user_message, messages)

    # 6) Save klaus response
    save_message_embedding(True, response, chat_id)
    return response
