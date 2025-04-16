import requests
import os

USER_ID = os.environ.get("HABITICA_USER_ID")
API_TOKEN = os.environ.get("HABITICA_API_TOKEN")

HEADERS = {
    "x-api-user": USER_ID,
    "x-api-key": API_TOKEN,
    "Content-Type": "application/json"
}

def get_tasks():
    url = "https://habitica.com/api/v3/tasks/user"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Error fetching tasks: {response.status_code}")

def format_tasks(tasks):
    """
    Formats tasks into a single string for use in the GPT prompt.
    Processes both 'todo' and 'daily' tasks.
    """
    priority_mapping = {
        0.1: "Trivial",
        1: "Easy",
        1.5: "Medium",
        2: "Hard"
    }

    todos_text = []
    for task in tasks:
        if task.get("type") == "todo":
            due_date = task.get("date")
            date_str = due_date if due_date else "no due date"
            status = "Done" if task.get("completed") else "To do"
            priority_value = task.get("priority", 1)
            priority_label = priority_mapping.get(priority_value, "Unknown")
            task_info = (
                f"{task.get('text')} (todo) - {status} - "
                f"Priority: {priority_label} - Due: {date_str}"
            )
            todos_text.append(task_info)

    dailies_text = []
    for task in tasks:
        if task.get("type") == "daily":
            is_due = task.get("isDue", False)
            completed = task.get("completed", False)

            if is_due and not completed:
                status_emoji = "⌛"
                status_text = "To do today"
            elif is_due and completed:
                status_emoji = "✅"
                status_text = "Done today"
            elif not is_due and completed:
                status_emoji = "✅"
                status_text = "Done (not due today)"
            else:
                status_emoji = "🔵"
                status_text = "Not due today"

            task_info = f"{status_emoji} {task.get('text')} (daily) - {status_text}"
            dailies_text.append(task_info)

    # Combine both lists with semicolon separators
    tasks_text = ";".join(todos_text) + ";" + ";".join(dailies_text)
    return tasks_text

def create_task_todo(text, notes="", priority=1, iso_date=None):
    url = "https://habitica.com/api/v3/tasks/user"
    payload = {
        "type": "todo",
        "text": text,
        "notes": notes,
        "priority": priority
    }
    if iso_date:
        payload["date"] = iso_date  # Ex: "2025-04-20T12:00:00.000Z"

    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code != 201:
        raise Exception(f"Error creating task: {response.text}")

    return response.json()["data"]