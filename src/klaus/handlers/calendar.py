from handlers.utils import save_message_embedding
from externals.calendar_api import list_today_events, create_event


# Calendar handlers
def handle_list_calendar(chat_id: str, user_message: str) -> str:
    save_message_embedding(False, user_message, chat_id)
    try:
        events = list_today_events(chat_id)
        response = "Eventos de hoje:\n" + "\n".join(events)
    except Exception as e:
        response = "Parece que houve um erro ao acessar sua agenda. Para autorizar, digite \"Autorizar agenda\". Erro 001."
    save_message_embedding(True, response, chat_id)
    return response


def handle_create_calendar(chat_id: str, user_message: str, title: str, start: str, end: str) -> str:
    if not title:
        response = "Parece que você não especificou o título da agenda. Lembre-se de colocar o título do seu evento entre \"aspas\"."
        return response

    save_message_embedding(False, user_message, chat_id)
    try:
        create_event(chat_id, title, start, end)
        response = f"Evento '{title}' criado na sua agenda."
    except Exception as e:
        response = "Parece que houve um erro ao acessar sua agenda. Para autorizar, digite \"Autorizar agenda\". Erro 003."
    save_message_embedding(True, response, chat_id)
    return response