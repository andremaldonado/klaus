import chromadb
import os
import uuid
import pytz
import logging

from datetime import datetime
from google import genai
from google.cloud import firestore
from typing import Tuple, Dict, Any, List

from data.client import get_firestore_client


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Logging configuration
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def get_chroma_client(chat_id: str) -> chromadb.api.models.Collection:
    storage_path = os.getenv("CHROMA_STORAGE_PATH", "./storage/chroma")
    user_path = os.path.join(storage_path, str(chat_id))
    os.makedirs(user_path, exist_ok=True)
    return chromadb.PersistentClient(path=user_path)


def save_message(chat_id: str, role: str, text: str) -> Tuple[str, Dict[str, Any]]:
    data = {
        "chat_id": chat_id,
        "role": role,
        "text": text,
        "timestamp": datetime.now(TIMEZONE).isoformat()
    }
    firestore_client = get_firestore_client()
    doc_ref = firestore_client.collection("messages").add(data)
    return doc_ref[1].id, data


def generate_embedding(text: str) -> List[float]:
    result = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text)
    return result.embeddings[0].values


def save_embedding(text: str, chat_id: str, message_id: str) -> None:
    chroma_client = get_chroma_client(chat_id)
    collection = chroma_client.get_or_create_collection("memories")
    embedding = generate_embedding(text)
    uid = str(uuid.uuid4())

    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{
            "chat_id": chat_id,
            "message_id": message_id,
            "timestamp": datetime.now(TIMEZONE).isoformat()
        }],
        ids=[uid]
    )


def fetch_similar_memories(chat_id: str, query_text: str, top_k: int = 3) -> List[str]:
    chroma_client = get_chroma_client(chat_id)
    collection = chroma_client.get_or_create_collection("memories")
    query_embedding = generate_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    logger.info(f"Fetched {len(results.get('documents', [[]])[0])} similar memories for query: {query_text} on chat_id {chat_id}. These are the memories: {results.get('documents', [[]])[0]}")
    return results.get("documents", [[]])[0]


def get_latest_messages(chat_id: str, limit: int = 16) -> List[Dict[str, Any]]:
    try:
        firestore_client = get_firestore_client()
        messages_ref = firestore_client.collection("messages")
        messages_ref = messages_ref.where("chat_id", "==", chat_id)
        query = messages_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        results = query.stream()
        return [doc.to_dict() for doc in results]
    except Exception as e:
        logger.error(f"❌ Error fetching latest messages: {e}")
        return []