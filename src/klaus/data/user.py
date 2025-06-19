from schemas import User
from data.client import get_firestore_client

from datetime import datetime, timezone


def _get_user_doc(chat_id: str):
    firestore_client = get_firestore_client()
    return firestore_client.collection("users").document(chat_id)


def get_user_doc(chat_id: str) -> User:
    db_user = _get_user_doc(chat_id).get()
    if not db_user.exists:
        return None

    data = db_user.to_dict()
    user = User(
        chat_id=chat_id,
        name=data.get("name", ""),
        refresh_token=data.get("refresh_token", ""),
        email=data.get("email", ""),
        habitica_id=data.get("habitica_id", ""),
        habitica_token=data.get("habitica_token", ""),
        updated_at=data.get("updated_at", None)
    )
    return user


def save_user(user: User) -> None:
    db_user = _get_user_doc(user.chat_id)
    db_user.set({
        "name": user.name,
        "refresh_token": user.refresh_token,
        "email": user.email,
        "habitica_id": user.habitica_id,
        "habitica_token": user.habitica_token,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }, merge=True)  # Use merge=True to update existing fields without overwriting the entire document
    