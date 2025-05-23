import os
import requests
import base64
import logging

from data.memory import firestore_client
from schemas import AuthCodeRequest

from datetime import datetime, timezone
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from flask import jsonify
from pydantic import ValidationError


_TOKEN_URL = "https://oauth2.googleapis.com/token"


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)



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
        _TOKEN_URL,
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

    # Salva refresh_token e perfil no Firestore
    firestore_client.collection("users").document(chat_id).set({
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