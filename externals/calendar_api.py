import os
import pytz
import logging

from auth.utils import load_credentials

from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)


def list_today_events(chat_id: str) -> list[str]:
    try:
        creds = load_credentials(chat_id, SCOPES)
        logger.debug("▶️ [DEBUG] calling events().list with token:", creds.token)
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(TIMEZONE).isoformat()
        end = datetime.now(TIMEZONE).replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
        events = service.events().list(
            calendarId="primary", timeMin=now, timeMax=end,
            singleEvents=True, orderBy="startTime"
        ).execute().get("items", [])
        logger.debug("▶️ [DEBUG] raw calendar response:", events)
        if not events:
            return ["Nenhum evento para hoje."]
        return [
            f"📅 {e['summary']} – {datetime.fromisoformat(e['start'].get('dateTime', e['start'].get('date'))).strftime('%H:%M') if 'dateTime' in e['start'] else 'Dia todo'}"
            for e in events
        ]
    except Exception as e:
        logger.debug("❌ [ERROR] Error listing events:", repr(e))
        raise

def create_event(chat_id: str, summary: str, start: str, end: str) -> str:
    creds = load_credentials(chat_id, SCOPES)
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