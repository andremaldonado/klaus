import os
import jwt
import requests

from data.memory import firestore_client

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


TOKEN_URI = "https://oauth2.googleapis.com/token"


def _get_user_doc(chat_id: str):
    return firestore_client.collection("users").document(chat_id)


def extract_email_from_token(token: str) -> str:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("email")
    except Exception as e:
        raise Exception(f"Couldn't retrieve email from token: {e}")



def load_credentials(chat_id: str, scopes: list[str]) -> Credentials:
    doc = _get_user_doc(chat_id).get()
    if not doc.exists:
        raise Exception("User not authorized. Please login at the front-end.")
    data = doc.to_dict()
    refresh = data.get("refresh_token")
    if not refresh:
        raise Exception("No refresh token found. Please re-authorize.")

    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri=TOKEN_URI,
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=scopes,
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
        new_rt = getattr(creds, "refresh_token", None)
        if new_rt and new_rt != refresh:
            _get_user_doc(chat_id).update({"refresh_token": new_rt})
    return creds


def refresh_id_token(chat_id: str) -> str:
    doc = firestore_client.collection("users").document(chat_id).get()
    if not doc.exists:
        raise Exception("User not found. Please login at the front-end.")
    data = doc.to_dict()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise Exception("Unauthorized. Please login at the front-end.")

    resp = requests.post(TOKEN_URI, data={
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if resp.status_code != 200:
        raise Exception(f"Error renewing token: {resp.text}")

    return resp.json()["id_token"]
