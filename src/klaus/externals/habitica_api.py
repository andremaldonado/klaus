import requests
import os
import pytz
from rapidfuzz import fuzz
from typing import Any, Dict, List, Optional
from datetime import datetime


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))


def _get_headers(user_id: str, api_token: str) -> Dict[str, str]:
    return {
        "x-api-user": user_id,
        "x-api-key": api_token,
        "Content-Type": "application/json"
    }


def _get_tasks_from_habitica(user_id: str, api_token: str, today_only: bool = False) -> List[Dict[str, Any]]:

    url = "https://habitica.com/api/v3/tasks/user"
    if today_only:
        current_date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        url += f"?duedate={current_date}"
    response = requests.get(url, headers=_get_headers(user_id, api_token))
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Error fetching tasks: {response.status_code}")


def find_task_by_message(user_id: str, api_token: str, message: str, threshold: int = 80) -> Dict[str, Any]:
    # Searches 'todo' and 'daily' tasks for the best Levenshtein match to `message`.
    # Returns a dict with 'id', 'title' and 'score'. Raises if best score < threshold.
    best_score = 0
    best_task: Optional[Dict[str, Any]] = None

    tasks = _get_tasks_from_habitica(user_id, api_token)

    for t in tasks:
        if t.get("type") not in ("todo", "daily"):
            continue
        title = t.get("text", "")
        score = fuzz.ratio(message, title)
        if score > best_score:
            best_score = score
            best_task = t

    if not best_task or best_score < threshold:
        raise Exception(f"No matching task found for '{message}'. Best score: {best_score}%.")

    return {"id": best_task["_id"], "title": best_task["text"], "score": best_score}


def get_tasks(user_id: str, api_token: str, today_only: bool = False) -> str:   
    priority_mapping = {
        0.1: "Trivial",
        1: "Easy",
        1.5: "Medium",
        2: "Hard"
    }

    tasks = _get_tasks_from_habitica(user_id, api_token, today_only)

    todos_text: List[str] = []
    for task in tasks:
        if task.get("type") == "todo":
            due_date = task.get("date")
            date_str = due_date if due_date else "no due date"
            status = "Done" if task.get("completed") else "To do"
            priority_value = task.get("priority", 1)
            priority_label = priority_mapping.get(priority_value, "Unknown")
            todos_text.append(
                f"{task['text']} (todo) - {status} - "
                f"Priority: {priority_label} - Due: {date_str}"
            )

    dailies_text: List[str] = []
    for task in tasks:
        if task.get("type") == "daily":
            is_due = task.get("isDue", False)
            completed = task.get("completed", False)
            if is_due and not completed:
                status_emoji, status_text = "⌛", "Fazer hoje"
            elif is_due and completed:
                status_emoji, status_text = "✅", "Feita hoje"
            elif completed:
                status_emoji, status_text = "✅", "Feita (outro dia)"
            else:
                status_emoji, status_text = "🔵", "Não é para hoje"
            dailies_text.append(f"{status_emoji} {task['text']} (daily) - {status_text}")

    return ";".join(todos_text + dailies_text)


def create_task_todo(user_id: str, api_token: str, text: str, notes: str = "", priority: float = 1, iso_date: Optional[str] = None) -> Dict[str, Any]:
    
    url = "https://habitica.com/api/v3/tasks/user"
    payload = {"type": "todo", "text": text, "notes": notes, "priority": priority}
    if iso_date:
        payload["date"] = iso_date

    response = requests.post(url, headers=_get_headers(user_id, api_token), json=payload)
    if response.status_code != 201:
        raise Exception(f"Error creating task: {response.text}")

    return response.json()["data"]


def complete_task(user_id: str, api_token: str, task_id: str) -> Dict[str, Any]:

    url = f"https://habitica.com/api/v3/tasks/{task_id}/score/up"
    response = requests.post(url, headers=_get_headers(user_id, api_token))
    if response.status_code != 200:
        raise Exception(f"Error completing task: {response.text}")
    
    return response.json()["data"]
