import functions_framework
from habitica_api import get_tasks
from ai_assistant import generate_chatgpt_suggestion
from handlers.telegram_handler import handle_telegram_request

@functions_framework.http
def webhook(request):
    """
    Entry point for HTTP requests. Dispatches requests based on the source.
    Defaults to the Telegram handler if the source is not specified.
    """
    source = request.args.get("source", "telegram").lower()
    
    if source == "telegram":
        return handle_telegram_request(request)
    else:
        try:
            body = request.get_json(silent=True)
            if not body:
                return "No body", 400

            user_context = body.get("text", "What are my tasks?")
            tasks = get_tasks()
            response = generate_chatgpt_suggestion(tasks, user_context)
            return response, 200
        except Exception as e:
            return f"Error: {str(e)}", 500