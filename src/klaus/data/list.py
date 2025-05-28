import pytz
import os
import logging

from datetime import datetime
from data.client import get_firestore_client
from google.cloud.firestore_v1.collection import CollectionReference


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


def _get_items_ref(chat_id: str, list_name: str) -> CollectionReference:
    return _get_list_ref(chat_id, list_name).collection("items")


def _get_list_item_ref(chat_id: str, list_name: str, item_description: str): 
    try:
        items = _get_items_ref(chat_id, list_name)
        if not items:
            return None
        for doc in items.stream():
            if doc.to_dict()["text"] == item_description:
                return doc  # Return the DocumentReference to use .delete()
        return None
    except Exception as e:
        logger.error(f"❌ [ERROR] Error trying to find list item from list: {e}")
        return None


def add_items_to_list(chat_id: str, list_name: str, items: list[str]):
    items_ref = _get_items_ref(chat_id, list_name)
    for text in items:
        items_ref.add({
            "text": text,
            "createdAt": datetime.now(TIMEZONE)
        })


def remove_items_from_list(chat_id: str, list_name: str, items: list[str]):
    deleted_items = []
    for item in items:
        item_found = _get_list_item_ref(chat_id, list_name, item)
        if item_found: 
            item_found.reference.delete()
            deleted_items.append(item_found.to_dict()['text'])
        logger.warning(f"▶️ [DEBUG] List item \"{item}\" not found on list \"{list_name}\" for chat_id: {chat_id}")
    return deleted_items


def get_list(chat_id: str, list_name: str) -> list[dict]:
    docs = list(_get_items_ref(chat_id, list_name).stream())
    return [{"id": doc.id, "text": doc.to_dict()["text"]} for doc in docs]