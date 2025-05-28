from datetime import datetime, timedelta

from data.memory import save_message, save_embedding 


# Common functions
def parse_iso_date(date_text: str) -> str | None:
    """
    Converts Portuguese date keywords into an ISO-8601 string.
    Supports 'hoje' and 'amanhã'.
    """
    if not date_text:
        return None
    now = datetime.now(TIMEZONE)
    key = date_text.strip().lower()
    if key == "hoje":
        return now.isoformat() + "Z"
    if key == "amanhã":
        return (now + timedelta(days=1)).isoformat() + "Z"
    return None


def save_message_embedding(bot_role: bool, text: str, chat_id: str) -> str:
    # Save message and embedding to the database
    role = "user"
    if bot_role: role = "klaus"
    message_id, saved_data = save_message(chat_id, role, text)
    if role == "user":
        save_embedding(text, chat_id, message_id)
