import chromadb
import os
import uuid
from datetime import datetime, timezone
from google import genai
from google.cloud import firestore
from typing import Tuple, Dict, Any, List, Optional


# Database configuration
firestore_client = firestore.Client(project=os.getenv("DB_PROJECT_ID"), database=os.getenv("DB_NAME"))

# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ChromaDB Configuration
storage_path = os.getenv("CHROMA_STORAGE_PATH", "./storage/chroma")
os.makedirs(storage_path, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=storage_path)
collection = chroma_client.get_or_create_collection(name="memories")


def save_message(role: str, text: str) -> Tuple[str, Dict[str, Any]]:
    data = {
        "role": role,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    doc_ref = firestore_client.collection("messages").add(data)
    return doc_ref[1].id, data


def generate_embedding(text: str) -> List[float]:
    result = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text)
    return result.embeddings[0].values


def save_embedding(text, chat_id, message_id):
    embedding = generate_embedding(text)
    uid = str(uuid.uuid4())

    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{
            "chat_id": chat_id,
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }],
        ids=[uid]
    )


def fetch_similar_memories(query_text: str, top_k: int = 3) -> List[str]:
    query_embedding = generate_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results.get("documents", [[]])[0]
