import pytz
import os
import logging

from ai_assistant import chat, check_intents
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
    save_message_embedding(False, user_message, chat_id)
    
    memory_block = ""

    # Fetch context of similar memories
    relevant_memories = fetch_similar_memories(chat_id, user_message, 15)
    if relevant_memories:
        memory_block += "\n\nContexto importante de mensagens anteriores, não ignore este contexto ao respoder:\n"
        memory_block = "\n".join(relevant_memories)

    # Fetch latest messages
    latest_messages = get_latest_messages(chat_id)
    if len(latest_messages) > 0:
        memory_block += "\n\nMensagens mais recentes que vocês trocaram, da mais recente para a mais antiga, considere isso para que a conversa seja fluida:\n"
        for message in reversed(latest_messages): 
            if message["role"] == "user":
                memory_block += f"Usuário: {message['text']}\n"
            else:
                memory_block += f"Klaus: {message['text']}\n"

    # Check for calendar and task intents to include in the memory block
    intents = check_intents(user_message)
    if "calendar" in intents:
        events = list_today_events(chat_id)
        if events:
            memory_block += "\n\nEventos do usuário em sua agenda, caso seja útil:"
            memory_block += f"\n{events}"
    if "tasks" in intents:
        tasks = get_tasks()
        if tasks:
            memory_block += "\n\nTarefas do usuário em sua lista de tarefas, caso seja útil:"
            memory_block += f"\n{tasks}"

    # Generate response
    logger.debug(f"▶️ [DEBUG] memory_block = {memory_block}")
    response = chat(user_message, memory_block)
    save_message_embedding(True, response, chat_id)
    return response
