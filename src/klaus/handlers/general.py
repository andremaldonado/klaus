import pytz
import os
import logging

from handlers.ai_assistant import chat, check_intents
from data.memory import fetch_similar_memories, get_latest_messages
from handlers.utils import save_message_embedding
from externals.habitica_api import get_tasks
from externals.calendar_api import list_today_events
from data.message import get_pending_message, mark_message_as_sent


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


# General handler
def handle_general_chat(chat_id: str, user_message: str) -> str:
    
    # 1) Fetch latest messages
    messages = []
    history = get_latest_messages(chat_id, 10) 
    if history:
        messages.append({
            "role": "system",
            "content": "--- HISTÓRICO DE MENSAGENS (ordenado) ---"
        })
        for msg in history:
            role = msg["role"]
            if role == "klaus":
                role = "system" # retrocompatibility only
            messages.append({"role": role, "content": f"[{msg["timestamp"]}] {role}: {msg["text"]}"})


    # 2) Fetch context of similar memories
    relevant_memories = fetch_similar_memories(chat_id, user_message, 15)
    if relevant_memories:
        messages.append({
            "role": "system",
            "content": "--- MEMÓRIAS RELEVANTES ---"
        })
        for memory in relevant_memories:
            messages.append({
                "role": "system",
                "content": f"• {memory}"
            })

    # 3) Check for calendar and task intents to include in the context
    intents = check_intents(user_message)
    if "calendar" in intents:
        events = list_today_events(chat_id)
        if events:
            messages.append({
                "role": "system",
                "content": f"--- AGENDA DO USUÁRIO (se necessário) ---"
            })
            for event in events:
                messages.append({
                    "role": "system",
                    "content": f"• {event}"
                })
    if "tasks" in intents:
        tasks = get_tasks()
        if tasks:
            messages.append({
                "role": "system",
                "content": f"--- TAREFAS DO USUÁRIO (se necessário) ---"
            })
            for task in tasks:
                messages.append({
                    "role": "system",
                    "content": f"• {task}"
                })

    # 4) User message
    save_message_embedding(False, user_message, chat_id)

    # 5) Generate response
    response = chat(user_message, messages)

    # 6) Save klaus response
    save_message_embedding(True, response, chat_id)
    return response


def handle_get_message(chat_id: str) -> dict | None:
    message = get_pending_message(chat_id)

    if not message:
        return None
    
    mark_message_as_sent(chat_id, message["id"])
    save_message_embedding(True, message["text"], chat_id)
    payload = {
        "id": message["id"],
        "text": message["text"],
        "created_at": message.get("created_at")
    }
    return payload