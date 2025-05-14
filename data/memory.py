import chromadb
import os
import uuid
import pytz
from datetime import datetime, timezone
from google import genai
from google.cloud import firestore
from typing import Tuple, Dict, Any, List, Optional


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# Database configuration
firestore_client = firestore.Client(project=os.getenv("DB_PROJECT_ID"), database=os.getenv("DB_NAME"))

# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_chroma_client(chat_id: str) -> chromadb.api.models.Collection:
    storage_path = os.getenv("CHROMA_STORAGE_PATH", "./storage/chroma")
    user_path = os.path.join(storage_path, str(chat_id))
    os.makedirs(user_path, exist_ok=True)
    return chromadb.PersistentClient(path=user_path)


def save_message(role: str, text: str) -> Tuple[str, Dict[str, Any]]:
    data = {
        "role": role,
        "text": text,
        "timestamp": datetime.now(TIMEZONE).isoformat()
    }
    doc_ref = firestore_client.collection("messages").add(data)
    return doc_ref[1].id, data


def generate_embedding(text: str) -> List[float]:
    result = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text)
    return result.embeddings[0].values


def save_embedding(text, chat_id, message_id):
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


def fetch_similar_memories(chat_id, query_text: str, top_k: int = 3) -> List[str]:
    chroma_client = get_chroma_client(chat_id)
    collection = chroma_client.get_or_create_collection("memories")
    query_embedding = generate_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results.get("documents", [[]])[0]
