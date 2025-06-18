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


def _get_message_ref(chat_id: str) -> CollectionReference:
    return firestore_client \
        .collection("users") \
        .document(chat_id) \
        .collection("agent_messages")


def get_pending_message(chat_id: str) -> dict | None:
    docs = _get_message_ref(chat_id) \
        .where("sent", "==", False) \
        .order_by("created_at") \
        .limit(1) \
        .stream()
    for doc in docs:
        data = doc.to_dict()
        logger.debug(f"▶️ {datetime.now(TIMEZONE).strftime('%H:%M:%S')} - Mensagem encontrada: {data}")
        return {
            "id": doc.id,
            "text": data.get("text", ""),
            "created_at": data.get("created_at")
        }
    logger.debug(f"▶️ {datetime.now(TIMEZONE).strftime('%H:%M:%S')} - Mensagem não encontrada")
    return None



def mark_message_as_sent(chat_id: str, message_id: str):
    _get_message_ref(chat_id).document(message_id).update({"sent": True})
