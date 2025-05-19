import os
import pytz
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from data.memory import firestore_client


SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def _get_user_doc(chat_id: str):
    return firestore_client.collection("users").document(chat_id)

def _load_credentials(chat_id: str) -> Credentials:
    doc = _get_user_doc(chat_id).get()
    logger.debug(f"▶️ [DEBUG] chat_id = {chat_id}")
    logger.debug(f"▶️ [DEBUG] Firestore data = {doc.to_dict() if doc.exists else 'NO DOC'}")
    if not doc.exists:
        raise Exception("User not authorized. Please login at the front-end.")
    data = doc.to_dict()
    refresh_token = data.get("refresh_token")
    logger.debug(f"▶️ [DEBUG] refresh_token = {refresh_token!r}")
    if not refresh_token:
        raise Exception("No refresh token found. Please re-authorize.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES
    )
    # Atualiza access_token se expirado
    logger.debug("▶️ [DEBUG] creds before refresh:", creds) 
    if creds.expired or not creds.valid:
        try:
            creds.refresh(Request())
            logger.debug("▶️ [DEBUG] creds after refresh:", creds)
        except Exception as e:
            logger.debug("❌ [ERROR] refresh failed:", repr(e))
        # opcional: se rotation de refresh_token, salve new refresh_token:
        new_rt = getattr(creds, "refresh_token", None)
        if new_rt and new_rt != refresh_token:
            _get_user_doc(chat_id).update({"refresh_token": new_rt})
    return creds

def list_today_events(chat_id: str) -> list[str]:
    try:
        creds = _load_credentials(chat_id)
        logger.debug("▶️ [DEBUG] calling events().list with token:", creds.token)
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(TIMEZONE).isoformat()
        end = (datetime.now(TIMEZONE) + timedelta(days=1)).isoformat()
        events = service.events().list(
            calendarId="primary", timeMin=now, timeMax=end,
            singleEvents=True, orderBy="startTime"
        ).execute().get("items", [])
        logger.debug("▶️ [DEBUG] raw calendar response:", events)
        if not events:
            return ["Nenhum evento para hoje."]
        return [
            f"{e['summary']} – { e['start'].get('dateTime', e['start'].get('date')) }"
            for e in events
        ]
    except Exception as e:
        logger.debug("❌ [ERROR] Error listing events:", repr(e))
        raise

def create_event(chat_id: str, summary: str, start: str, end: str) -> str:
    creds = _load_credentials(chat_id)
    service = build("calendar", "v3", credentials=creds)

    start_dt = TIMEZONE.localize(datetime.strptime(start, "%d/%m/%Y %H:%M"))
    end_dt   = TIMEZONE.localize(
        datetime.strptime(end, "%d/%m/%Y %H:%M")
    ) if end else start_dt + timedelta(hours=1)

    event = {
        "summary": summary,
        "start":   {"dateTime": start_dt.isoformat(), "timeZone": str(TIMEZONE)},
        "end":     {"dateTime": end_dt.isoformat(),   "timeZone": str(TIMEZONE)},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Evento criado: {created.get('htmlLink')}"