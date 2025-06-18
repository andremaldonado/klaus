import os
import logging


from handlers.ai_assistant import chat
from data.list import get_list, add_items_to_list, remove_items_from_list
from handlers.utils import save_message_embedding
from data.list import remove_items_from_list


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


# List handlers
def handle_create_list_item(chat_id: str, user_message: str, title: str, items: list[str]) -> str:
    if not items:
        response = "Parece que você não especificou nenhum item para adicionar à lista. Para fazer isso, digite o que você quer adicionar à lista entre \"aspas\"."
        return response

    save_message_embedding(False, user_message, chat_id)
    response = ""
    try:
        add_items_to_list(chat_id, title, items)
        response = f"Tá feito! Inclui o(s) item(ns) abaixo:\n\n"
        response += "\n - ".join(items)
        response += f"\n\nNa lista \"{title}\"."
    except Exception as e:
        response = "Parece que houve um erro ao criar o item na lista."
        logger.error(f"❌ [ERROR] Error creating list item: {e}")
        return response
    
    if not response:
        response = "Parece que houve um erro ao criar o item na lista."
        logger.warning(f"⚠️ [WARNING] Empty list item: {e}")

    save_message_embedding(True, response, chat_id)
    return response


def handle_list_user_list_items(chat_id: str, user_message: str, title: str) -> str:
    save_message_embedding(False, user_message, chat_id)
    response = ""
    try:
        items = get_list(chat_id, title)
        if items:
            response = f"A lista \"{title.capitalize()}\" contém os seguintes itens:\n"
            items_list = [f"- {item['text'].capitalize()}" for item in items]
            response += "\n".join(items_list)
            save_message_embedding(True, response, chat_id)
            return response
    except Exception as e:
        response = "Parece que houve um erro ao acessar a lista de itens."
        logger.error(f"❌ [ERROR] Error accessing list: {e}")
        return response
    
    response = "Sua lista não existe ou está vazia. Que tal começar uma nova lista?"
    save_message_embedding(True, response, chat_id)
    return response


def handle_remove_list_item(chat_id: str, user_message: str, title: str, items: list[str]) -> str:
    if not items:
        response = "Parece que você não especificou nenhum item para remover da lista. Para fazer isso, digite o que você quer remover da lista entre \"aspas\"."
        return response

    save_message_embedding(False, user_message, chat_id)
    response = ""
    try:
        deleted_items = remove_items_from_list(chat_id, title, items)
        if deleted_items:
            response = "\nOs itens excluídos foram os seguintes:\n"
            response += "\n - ".join(deleted_items)
        else:
            response = "\nTivemos um erro e não conseguimos excluir nada.\n"    
    except Exception as e:
        response = "Parece que houve um erro ao remover os itens da lista."
        logger.error(f"❌ [ERROR] Error removing list items: {e}")
        return response

    if not response:
        response = "Parece que houve um erro ao remover os itens da lista."
        logger.warning("⚠️ [WARNING] Empty response after attempting to remove list items.")

    save_message_embedding(True, response, chat_id)
    return response