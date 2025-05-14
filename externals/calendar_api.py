import os
import pytz
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


#Constants
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_DIR = os.getenv("GOOGLE_TOKENS_DIR", "tokens")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


def _get_token_path(chat_id: int) -> str:
    os.makedirs(TOKEN_DIR, exist_ok=True)
    return os.path.join(TOKEN_DIR, f"token_{chat_id}.json")


def _load_credentials(chat_id: int) -> Credentials:
    token_path = _get_token_path(chat_id)
    if not os.path.exists(token_path):
        raise Exception("User not authorized. Please authorize first.")
    return Credentials.from_authorized_user_file(token_path, SCOPES)


def generate_authorization_url(chat_id: int) -> str:
    os.makedirs(TOKEN_DIR, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(
        GOOGLE_CREDENTIALS,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url


def exchange_code_for_token(chat_id: int, code: str):
    flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS, SCOPES,redirect_uri="urn:ietf:wg:oauth:2.0:oob")
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_path = _get_token_path(chat_id)
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())


def list_today_events(chat_id: int) -> List[str]:
    try:
        creds = _load_credentials(chat_id)
        service = build("calendar", "v3", credentials=creds)

        now = datetime.now().isoformat() + "Z"
        end = (datetime.now() + timedelta(days=1)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return ["Nenhum evento para hoje."]
        return [f"{e['summary']} - {e['start'].get('dateTime', e['start'].get('date'))}" for e in events]
    except Exception as e:
        return ["Nenhum evento para hoje ou agenda não autorizada."]


def create_event(chat_id: int, summary: str, start: str, end: str) -> str:
    try:
        creds = _load_credentials(chat_id)
        service = build("calendar", "v3", credentials=creds)

        start_datetime = datetime.strptime(start, "%d/%m/%Y %H:%M")
        start_datetime = TIMEZONE.localize(start_datetime)
        print("Localized start datetime:", start_datetime)

        if not end:
            end_datetime = start_datetime + timedelta(hours=1)
        else:
            end_datetime = TIMEZONE.localize(datetime.strptime(end, "%d/%m/%Y %H:%M"))

        print("Creating event with start:", start, "and end:", end)
        event = {
            "summary": summary,
            "start": {"dateTime": start_datetime.isoformat(), "timeZone": os.getenv("TIMEZONE", "America/Sao_Paulo")},
            "end": {"dateTime": end_datetime.isoformat(), "timeZone": os.getenv("TIMEZONE", "America/Sao_Paulo")},
        }

        result = service.events().insert(calendarId="primary", body=event).execute()
    except Exception as e:
        print("Error creating event:", e)
        raise Exception("Error creating event. Please check your calendar settings.")
    
    print("Event created:", result)
    return result.get("htmlLink", "Evento criado.")