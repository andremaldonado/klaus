import os
from datetime import datetime
from openai import OpenAI
from habitica_api import format_tasks

def generate_chatgpt_suggestion(tasks, user_context):
    """
    Generates a suggestion using ChatGPT based on the provided tasks and user context.
    """
    tasks_text = format_tasks(tasks)
    today_date = datetime.now().strftime("%d/%m/%Y")
    
    system_context = (
        "You are Klaus, a calm, polite, and objective personal assistant. "
        "Your mission is to analyze the user's tasks and provide practical suggestions. "
        "Always use a respectful, yet concise tone.\n\n"
        "=== Telegram Formatting Instructions ===\n"
        "- Use plain text. You may use line breaks to separate topics.\n"
        "- Avoid Markdown formatting.\n"
        "- Use emojis to indicate priority and status.\n\n"
        f"Today is {today_date}. Below are the user's tasks, separated by semicolons:\n"
        f"{tasks_text}\n\n"
        "=== Example Response ===\n"
        "Good morning! You have some pending tasks today. "
        "I suggest starting with the tasks that have the closest or overdue due dates. "
        "Then, if you have time, move on to the others. "
        "Avoid letting tasks accumulate for several days.\n\n"
        "Please prioritize urgent or high-impact tasks, and maintain a positive tone. "
        "Respond considering the user's context and the listed tasks."
    )

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": system_context},
            {"role": "user",   "content": user_context}
        ],
        temperature=0.5
    )

    return response.output_text
