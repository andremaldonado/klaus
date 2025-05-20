import json
import os
import pytz
from datetime import datetime, timezone
from externals.habitica_api import format_tasks
from google import genai
from typing import List, Dict, Any


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))
TODAY_DATE = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
BASIC_INSTRUCTIONS = (
    "Você é Klaus, um assistente pessoal calmo, educado e objetivo.\n"
    "Sua missão é manter uma conversa agradável e útil com o usuário, sempre com um tom respeitoso e conciso.\n"
    f"Hoje é {TODAY_DATE}.\n\n"
    "=== Instruções de Formatação da resposta ===\n"
    "- Use texto simples. Você pode usar quebras de linha para separar tópicos.\n"
    "- Evite formatação em Markdown.\n"
    "- Use emojis quando entender ser necessário.\n\n"
)


# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def chat(message: str, context: str) -> str:
    # Generates a message using the Gemini API based on the provided user message.
    
    ai_prompt_system_context = (
        BASIC_INSTRUCTIONS +
        "A seguir, você encontrará o contexto das conversas anteriores do usuário:\n"
        f"{context}\n\n"
        "Com base nesse contexto, responda à mensagem do usuário de forma natural e envolvente. "
        "Você pode fazer perguntas, oferecer sugestões ou simplesmente continuar a conversa de maneira fluida.\n"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=message,
        config=genai.types.GenerateContentConfig(
            system_instruction=ai_prompt_system_context,
            temperature=2.0
        )
    )

    return response.text


def generate_tasks_suggestion(tasks: List[Dict[str, Any]], events: str, user_context: str) -> str:
    # Generates a suggestion using ChatGPT based on the provided tasks and user context.
    tasks_text = format_tasks(tasks)
    today_date = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
    
    ai_prompt_system_context = (
        BASIC_INSTRUCTIONS +
        "=== Instruções de Resposta ===\n"
        f"Abaixo estão as tarefas do usuário, separadas por ponto e vírgula:\n"
        f"{tasks_text}\n\n"
        "Abaixo está a agenda do usuário:\n"
        f"{events}\n\n"
        "Responda à solicitação do usuário considerando o contexto do usuário e as tarefas listadas.\n"
        "Note que podem existir tarefas e eventos para outros dias ou que já foram finalizados.\n" 
        "Considere isso para responder ao usuário de acordo com a solicitação dele.\n"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_context,
        config=genai.types.GenerateContentConfig(
            system_instruction=ai_prompt_system_context,
            temperature=0.5
        )
    )

    return response.text


def interpret_user_message(user_message: str) -> Dict[str, Any]:
    # Interprets the user message to determine his intent or is unrelated. It returns a structured JSON with
    # the following fields:
    
    today_date = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
    ai_prompt_engineering_prompt = (
        f"""Aja como um especialista em interpretação de linguagem natural e extração de informações a partir de mensagens de texto. 
        Sua tarefa é classificar a intenção da mensagem do usuário e extrair informações relevantes.
        INSTRUÇÃO

        Você receberá uma mensagem de usuário. Sua tarefa é determinar se a mensagem:

        - Refere-se à criação de uma nova tarefa.
        - Solicita o status de tarefas existentes.
        - Solicita a conclusão de uma tarefa.
        - Solicita a listagem de eventos do Google Calendar.
        - Solicita a criação de um evento no Google Calendar.
        - Não está relacionada a nenhuma das anteriores.

        Você DEVE extrair os seguintes campos e retorná-los em JSON no seguinte formato:

        {{
        "message": [mensagem original do usuário],
        "type": ["new_task" | "task_status" | "task_conclusion" | "unrelated"],
        "title": [título resumido da tarefa, nome do evento para o calendário ou null],
        "start_date": [data de início do evento, no formato dd/mm/aaaa hh:mm ou null],
        "end_date": [data de término do evento, no formato dd/mm/aaaa hh:mm ou null],
        "priority": ["low" | "medium" | "high" | null]
        "details": [detalhes adicionais ou null]
        }}

        É imprescindível que esse retorno não tenha nenhuma formatação, nem mesmo algo como ```json.

        Seja rigoroso em sua classificação. Se uma mensagem for ambígua ou não se referir claramente a uma tarefa, 
        status de tarefa ou item de calendário, classifique-a como "unrelated".

        Ao extrair a prioridade, considere não apenas palavras-chave explícitas, mas também a urgência implícita no tom. Por exemplo:

        - "preciso muito", "urgente", "o quanto antes" → high  
        - "se possível", "talvez", "mais tarde" → low

        Mantenha o texto original em português nos campos "message" e "title". 
        Para os campos start_date e end_date, use as datas que o usuário fornecer, as que coloquei no exemplo são apenas exemplos de formatação e não as datas que você precisa enviar.

        EXEMPLOS

        Usuário: "Crie a seguinte tarefa: ir na academia hoje"  
        Saída: {{ "message": "Preciso ir na academia hoje", "type": "new_task", "title": "ir na academia", "start_date": "10/10/2023", "end_date": null, "priority": null, "details": null }}

        Usuário: "Quais tarefas minhas estão atrasadas?"  
        Saída: {{ "message": "Quais tarefas minhas estão atrasadas?", "type": "task_status", "title": null, "start_date": null, "end_date": null, "priority": null, "details": null }}

        Usuário: "Tenho tarefas para hoje? Quais?"  
        Saída: {{ "message": "Tenho tarefas para hoje? Quais?", "type": "task_status", "title": null, "start_date": "10/10/2023", "end_date": null, "priority": null, "details": null }}

        Usuário: "A pizza chegou"  
        Saída: {{ "message": "A pizza chegou", "type": "unrelated", "title": null, "start_date": null, "end_date": null, "priority": null, "details": null }}

        Usuário: "Terminei de ler o livro"
        Saída: {{ "message": "Terminei de ler o livro", "type": "task_conclusion", "title": "ler o livro", "start_date": null, "end_date": null, "priority": null, "details": null }}

        Usuário: "Já fiz a lição"
        Saída: {{ "message": "Já fiz a lição", "type": "task_conclusion", "title": "lição", "start_date": null, "end_date": null, "priority": null, "details": null }}

        Usuário: "Quais eventos tenho hoje?"
        Saída: {{ "message": "Quais eventos tenho hoje?", "type": "list_calendar", "title": null, "start_date": "10/05/2024", "end_date": null, "priority": null, "details": null }}

        Usuário: "Preciso cortar o cabelo amanhã às 15:00"
        Saída: {{ "message": "Preciso cortar o cabelo amanhã às 15:00", "type": "create_calendar", "title": "cortar o cabelo", "start_date": "11/07/2025 15:00", "end_date": null, "priority": null, "details": null }}

        Usuário: "Reunião de trabalho das 14:00 às 15:30 no dia 10/10/2023"
        Saída: {{ "message": "Reunião de trabalho das 14:00 às 15:30 no dia 10/10/2023", "type": "create_calendar", "title": "Reunião de trabalho", "start_date": "10/10/2023 14:00", "end_date": "10/10/2023 15:30", "priority": null, "details": null }}

        FIM

        Informações adicionais que podem ser relevantes:
         - Hoje é dia {today_date}

        Agora, processe a seguinte mensagem de acordo com as instruções."""
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=user_message,
        config=genai.types.GenerateContentConfig(
            system_instruction=ai_prompt_engineering_prompt,
            temperature=0.0
        )
    )

    result_text = response.text
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        result = {
            "message": user_message,
            "type": "unrelated",
            "title": None,
            "start_date": None,
            "end_date": None,
            "priority": None,
            "details": None
        }
    return result