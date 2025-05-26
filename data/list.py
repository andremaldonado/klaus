import pytz
import os
import logging

from datetime import datetime
from data.utils import get_firestore_client


TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)

firestore_client = get_firestore_client()

def _get_list_ref(chat_id: str, list_name: str):
    return firestore_client \
        .collection("users") \
        .document(chat_id) \
        .collection("lists") \
        .document(list_name.lower())


def _get_items_ref(chat_id: str, list_name: str):
    return _get_list_ref(chat_id, list_name) \
        .collection("items")


def add_items_to_list(chat_id: str, list_name: str, items: list[str]):
    items_ref = _get_items_ref(chat_id, list_name)
    for text in items:
        logger.debug(f"▶️ [DEBUG] Adding item: {text} to list: {list_name} for chat_id: {chat_id}")
        items_ref.add({
            "text": text,
            "createdAt": datetime.now(TIMEZONE)
        })


def remove_item_from_list(chat_id: str, list_name: str, item_id: str):
    return _get_items_ref(chat_id, list_name).document(item_id).delete()


def get_list(chat_id: str, list_name: str) -> list[str]:
    docs = list(_get_items_ref(chat_id, list_name).stream())
    return [doc.to_dict()["text"] for doc in docs]