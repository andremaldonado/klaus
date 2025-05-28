from data.client import get_firestore_client

def get_user_doc(chat_id: str):
    firestore_client = get_firestore_client()
    return firestore_client.collection("users").document(chat_id)