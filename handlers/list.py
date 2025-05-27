import os
import logging


from ai_assistant import chat
from data.list import get_list, add_items_to_list
from handlers.utils import save_message_embedding


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
        context = f"Parece que o usuário solicitou que você criasse os itens abaixo na lista \"{title}\":\n"
        context += "\n - ".join(items)
        context += "Responda ao usuário que os itens foram criados com sucesso.\n"
        context += "Inclua o que mais achar necessário dado o contexto da mensagem.\n\n"
        response = chat(user_message, context)
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
            context = "O usuário solicitou que você listasse os itens da lista.\n"
            context += f"A lista \"{title}\" contém os seguintes itens:\n"
            items_list = [f"- {item['id']}: {item['text']}" for item in items]
            context = "\n".join(items_list)
            context += "Responda ao usuário com os itens listados de forma clara e concisa.\n"
            context += "Você pode também sugerir que o usuário adicione novos itens à lista ou faça outras ações relacionadas.\n"
            context += "Liste os itens no seguinte formato: - [ID] Item da lista \n"
            context += "Inclua o que mais achar necessário dado o contexto da mensagem.\n\n"
            response = chat(user_message, context)
            save_message_embedding(True, response, chat_id)
            return response
    except Exception as e:
        response = "Parece que houve um erro ao acessar a lista de itens."
        logger.error(f"❌ [ERROR] Error accessing list: {e}")
        return response
    
    response = "Sua lista não existe ou está vazia. Que tal começar uma nova lista?"
    save_message_embedding(True, response, chat_id)
    return response