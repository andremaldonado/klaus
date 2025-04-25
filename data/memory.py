import os
import uuid
from datetime import datetime
from google.cloud import firestore
from typing import Tuple, Dict, Any, List, Optional


firestore_client = firestore.Client(project=os.getenv("DB_PROJECT_ID"), database=os.getenv("DB_NAME"))


def save_message(role: str, text: str) -> Tuple[str, Dict[str, Any]]:
    data = {
        "role": role,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    doc_ref = firestore_client.collection("messages").add(data)
    return doc_ref[1].id, data


def get_latest_messages(limit: int = 5) -> List[Dict[str, Any]]:
    messages_ref = firestore_client.collection("messages")
    query = messages_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    results = query.stream()
    return [doc.to_dict() for doc in results]