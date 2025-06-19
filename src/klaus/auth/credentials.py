import base64
import os
import jwt

from data.user import get_user_doc, save_user

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


TOKEN_URI = "https://oauth2.googleapis.com/token"


def sanitize_id(raw: str) -> str:
    token = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    return token.rstrip("=")


def extract_email_from_token(token: str) -> str:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("email")
    except Exception as e:
        raise Exception(f"Couldn't retrieve email from token: {e}")



def load_credentials(chat_id: str, scopes: list[str]) -> Credentials:
    user = get_user_doc(chat_id)
    if not user:
        raise Exception("User not authorized. Please login at the front-end.")
    refresh = getattr(user, "refresh_token", None)
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
            user.refresh_token = new_rt
            save_user(user)
    return creds
