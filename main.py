import functions_framework
from datetime import datetime, timedelta
from habitica_api import get_tasks, find_task_by_message, create_task_todo, complete_task
from ai_assistant import generate_chatgpt_suggestion, interpret_user_message, chat
from handlers.telegram_handler import validate_telegram_request, send_telegram_message

@functions_framework.http
def webhook(request):
    """
    Entry point for HTTP requests.
    First, validates the request if it comes from Telegram.
    Then, interprets the user message and, based on its type:
      - For "task_status": fetch tasks and generate a GPT suggestion.
      - For "new_task": creates a new task using Habitica's API.
      - Otherwise: returns a message indicating that the message is unrelated.
    For Telegram requests, the response is also sent via Telegram.
    """

    source = request.args.get("source", "telegram").lower()
    
    telegram_chat_id = None
    if source == "telegram":
        validation = validate_telegram_request(request)
        if not validation.get("valid"):
            return validation.get("message"), validation.get("status_code")
        telegram_chat_id = validation.get("chat_id")
    
    try:
        body = request.get_json(silent=True)
        if not body:
            return "No body", 400

        user_message = body.get("message", "")
        user_message = user_message.get("text", "What are my tasks?")

        # First, interpret the user message (for any source)
        interpretation = interpret_user_message(user_message)
        message_type = interpretation.get("type")

        response_message = ""
        
        if message_type == "task_status":
            tasks = get_tasks()
            response_message = generate_chatgpt_suggestion(tasks, user_message)
        elif message_type == "new_task":
            # For task creation, extract the task title, priority and date from the interpretation
            task_title = interpretation.get("task") or user_message
            
            # Map priority string to numeric value.
            priority_text = interpretation.get("priority")
            priority_mapping = {"low": 0.1, "medium": 1, "high": 2}
            priority_value = priority_mapping.get(priority_text, 1)
            
            # Convert date from natural language to ISO format if possible.
            date_text = interpretation.get("date")
            iso_date = None
            if date_text:
                dt_now = datetime.now()
                if date_text.lower() == "hoje":
                    iso_date = dt_now.isoformat() + "Z"
                elif date_text.lower() == "amanhã":
                    iso_date = (dt_now + timedelta(days=1)).isoformat() + "Z"
            
            # Create the new task using Habitica API.
            created_task = create_task_todo(task_title, notes="", priority=priority_value, iso_date=iso_date)
            response_message = "Tarefa criada! Vamos em frente!"
        elif message_type == "task_conclusion":
            task_title = interpretation.get("task")
            # Find out which task to mark as completed.
            tasks = get_tasks()
            task = find_task_by_message(tasks, task_title)
            task_id = task.get("id")
            # Mark the task as completed using Habitica API.
            complete_task(task_id)
            response_message = f"Tarefa \"{task.get('title')}\" concluída! Bom trabalho!"
        else:
            response_message = chat(user_message)

        # If source is telegram, send the message via Telegram.
        if source == "telegram" and telegram_chat_id:
            send_telegram_message(telegram_chat_id, response_message)
            return "Message sent via Telegram.", 200

        # For non-Telegram sources, return the response in the HTTP body.
        return response_message, 200

    except Exception as e:
        return f"Error: {str(e)}", 500
