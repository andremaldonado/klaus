import os
import requests
import base64
import logging

from data.user import get_user_doc
from schemas import AuthCodeRequest
from auth.utils import extract_email_from_token, sanitize_id

from datetime import datetime, timezone
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from flask import jsonify
from pydantic import ValidationError
from typing import Any, Dict, Tuple, Union
from flask import Request


TOKEN_URI = "https://oauth2.googleapis.com/token"


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def _refresh_id_token(chat_id: str) -> str:
    doc = get_user_doc(chat_id).get()
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


def authenticate_request(auth_header) -> Tuple[int, Union[str, Dict[str, Any]]]:
    if not auth_header.startswith("Bearer "):
        logger.error(f"❌ [ERROR] Invalid authorization header: {auth_header}")
        return 401, None

    id_token_str = auth_header.split(" ", 1)[1]
    idinfo = None
    try:
        idinfo = get_id_info(id_token_str)
    except Exception as e:
        try:
            email_guess = extract_email_from_token(id_token_str)
            chat_id = sanitize_id(email_guess)
            id_token_str = _refresh_id_token(chat_id)
            idinfo = get_id_info(id_token_str)
        except Exception as refresh_error:
            logger.error(f"❌ [ERROR] Refresh token has failed: {refresh_error}")
            return 401, None
        
    if not idinfo:
        logger.error(f"❌ [ERROR] Invalid ID token: {id_token_str}")
        return 401, "Invalid ID token"
    
    email = idinfo.get("email")
    if not idinfo.get("email_verified"):
        logger.error(f"❌ [ERROR] Email not verified: {email}")
        return 403, None 

    allowed = os.getenv("ALLOWED_EMAILS", "").split(",")
    if email not in allowed:
        logger.critical(f"❌ [CRITICAL] Unauthorized email: {email}")
        return 403, None
    
    chat_id = sanitize_id(email)
    if not chat_id:
        logger.error(f"❌ [ERROR] Invalid chat_id: {chat_id}")
        return 401, None
    
    return 200, chat_id


def handle_google_auth(request):
    headers = {
        "Access-Control-Allow-Origin":      os.getenv("CORS_ALLOW_ORIGIN", "http://localhost:8081"),
        "Access-Control-Allow-Methods":     "POST, OPTIONS",
        "Access-Control-Allow-Headers":     "Content-Type",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age":           "3600"
    }

    if request.method == "OPTIONS":
        return ("", 204, headers)
    if request.method != "POST":
        return ("Method Not Allowed", 405, headers)
    
    body = request.get_json(silent=True) or {}
    try:
        auth_req = AuthCodeRequest(**body)
    except ValidationError as err:
        return (f"Bad Request: {err}", 400, headers)
    code = auth_req.code

    data = {
        "client_id":     os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "code":          code,
        "grant_type":    "authorization_code",
        "redirect_uri":  os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8081")
    }

    resp = requests.post(
        TOKEN_URI,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if resp.status_code != 200:
        if resp.status_code in (400, 401):
            return ("Invalid authorization code", 401, headers)
        return ("Bad Gateway: error fetching tokens", 502, headers)

    tokens = resp.json()
    idtok   = tokens["id_token"]
    refresh = tokens.get("refresh_token")
    if not refresh:
        return ("No refresh token returned", 502, headers)

    # Valida o ID token (JWT)
    try:
        idinfo = get_id_info(idtok)
    except Exception as e:
        logger.debug(f"❌ [ERROR] Invalid ID token: {e}")
        return ("Invalid ID token", 401, headers)

    email   = idinfo.get("email")
    name    = idinfo.get("name")
    chat_id = base64.urlsafe_b64encode(email.encode("utf-8")).decode("ascii").rstrip("=")

    # Salva refresh_token e perfil do usuário
    get_user_doc(chat_id).set({
        "email":         email,
        "name":          name,
        "refresh_token": refresh,
        "updated_at":    datetime.now(timezone.utc).isoformat()
    }, merge=True)

    logger.debug(f"▶️ [DEBUG] User {chat_id} ({email}) authorized with refresh token: {refresh!r}. Id token: {idtok!r}. Name: {name!r}")
    return (jsonify({"idToken": idtok, "email": email, "name": name}), 200, headers)


def get_id_info(id_token_str):
    idinfo = google_id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        os.getenv("GOOGLE_CLIENT_ID"),
        clock_skew_in_seconds=10 if _ENVIRONMENT == "dev" else 0
    )
    return idinfo