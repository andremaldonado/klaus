import requests
import os
import pytz
from rapidfuzz import fuzz
from typing import Any, Dict, List, Optional
from datetime import datetime


# Constants
USER_ID = os.environ.get("HABITICA_USER_ID")
API_TOKEN = os.environ.get("HABITICA_API_TOKEN")
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

HEADERS = {
    "x-api-user": USER_ID,
    "x-api-key": API_TOKEN,
    "Content-Type": "application/json"
}


def find_task_by_message(tasks: List[Dict[str, Any]], message: str, threshold: int = 80) -> Dict[str, Any]:
    # Searches 'todo' and 'daily' tasks for the best Levenshtein match to `message`.
    # Returns a dict with 'id', 'title' and 'score'. Raises if best score < threshold.
    best_score = 0
    best_task: Optional[Dict[str, Any]] = None

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


def get_tasks(today_only: bool = False) -> List[Dict[str, Any]]:
    url = "https://habitica.com/api/v3/tasks/user"
    if today_only:
        current_date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        url += f"?duedate={current_date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Error fetching tasks: {response.status_code}")


def format_tasks(tasks: List[Dict[str, Any]]) -> str:
    priority_mapping = {
        0.1: "Trivial",
        1: "Easy",
        1.5: "Medium",
        2: "Hard"
    }

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
                status_emoji, status_text = "⌛", "To do today"
            elif is_due and completed:
                status_emoji, status_text = "✅", "Done today"
            elif completed:
                status_emoji, status_text = "✅", "Done (not due today)"
            else:
                status_emoji, status_text = "🔵", "Not due today"
            dailies_text.append(f"{status_emoji} {task['text']} (daily) - {status_text}")

    return ";".join(todos_text + dailies_text)


def create_task_todo(text: str, notes: str = "", priority: float = 1, iso_date: Optional[str] = None) -> Dict[str, Any]:
    url = "https://habitica.com/api/v3/tasks/user"
    payload = {"type": "todo", "text": text, "notes": notes, "priority": priority}
    if iso_date:
        payload["date"] = iso_date

    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code != 201:
        raise Exception(f"Error creating task: {response.text}")

    return response.json()["data"]


def complete_task(task_id: str) -> Dict[str, Any]:
    url = f"https://habitica.com/api/v3/tasks/{task_id}/score/up"
    response = requests.post(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Error completing task: {response.text}")
    
    return response.json()["data"]
