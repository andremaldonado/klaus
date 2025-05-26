import json
import os
import pytz
import re

from dateparser import parse as dp_parse
from datetime import datetime, timezone, timedelta
from externals.habitica_api import format_tasks
from google import genai
from typing import List, Dict, Any, Optional


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))
TODAY_DATE = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
BASIC_INSTRUCTIONS = (
    "Você é Klaus, um assistente pessoal pronto para ajudar em qualquer tarefa que o usuário solicitar.\n"
    "Sua missão é manter uma conversa agradável e útil com o usuário, sempre com um tom respeitoso e conciso.\n"
    "Você pode responder perguntas, oferecer sugestões, criar tarefas, organizar eventos, manusear listas, e muito mais. \n"
    "Considere que sua memória é específica para o contexto do que o usuário está pedindo.\n"
    f"Hoje é {TODAY_DATE}.\n\n"
    "=== Instruções de Formatação da resposta ===\n"
    "- Use texto simples. Você pode usar quebras de linha para separar tópicos.\n"
    "- Evite formatação em Markdown.\n"
    "- Use emojis quando entender ser necessário.\n\n"
)

# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_list_items(text: str) -> List[str]:
    pattern = r'"([^"]+)"'
    return re.findall(pattern, text)


def chat(message: str, context: str) -> str:
    # Generates a message using the Gemini API based on the provided user message.
    
    ai_prompt_system_context = (
        BASIC_INSTRUCTIONS +
        "A seguir, você encontrará um contexto que pode ser importante para responder ao usuário:\n"
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
    text = user_message.strip()
    msg_lower = text.lower()
    
    start_iso: Optional[str] = None
    end_iso: Optional[str] = None

    interval_match = re.search(
        r'das?\s*(\d{1,2}:\d{2})\s*(?:às?|a)\s*(\d{1,2}:\d{2})(?:\s*no dia\s*(\d{1,2}/\d{1,2}/\d{2,4}))?',
        msg_lower
    )
    if interval_match:
        start_time = interval_match.group(1)
        end_time = interval_match.group(2)
        date_part = interval_match.group(3)
        if date_part:
            start_dt = dp_parse(f"{date_part} {start_time}", languages=['pt'], settings={'TIMEZONE': TIMEZONE.zone, 'RETURN_AS_TIMEZONE_AWARE': True})
            end_dt = dp_parse(f"{date_part} {end_time}", languages=['pt'], settings={'TIMEZONE': TIMEZONE.zone, 'RETURN_AS_TIMEZONE_AWARE': True})
        else:
            today_str = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
            start_dt = dp_parse(f"{today_str} {start_time}", languages=['pt'], settings={'TIMEZONE': TIMEZONE.zone, 'RETURN_AS_TIMEZONE_AWARE': True})
            end_dt = dp_parse(f"{today_str} {end_time}", languages=['pt'], settings={'TIMEZONE': TIMEZONE.zone, 'RETURN_AS_TIMEZONE_AWARE': True})
        if start_dt:
            start_iso = start_dt.strftime("%d/%m/%Y %H:%M")
        if end_dt:
            end_iso = end_dt.strftime("%d/%m/%Y %H:%M")
    else:
        date_match = re.search(
            r'((?:hoje|amanhã|ontem|próximo[oa]? [a-zç]+|\d{1,2}/\d{1,2}/\d{2,4})(?:\s*às?\s*(\d{1,2}:\d{2}))?)',
            msg_lower
        )
        if date_match:
            date_str = date_match.group(1)
            hour_str = date_match.group(2)
            dt = dp_parse(
                date_str,
                languages=['pt'],
                settings={
                    'TIMEZONE': TIMEZONE.zone,
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
                )
            if dt:
                if hour_str:
                    hour, minute = map(int, hour_str.split(":"))
                    dt = dt.replace(hour=hour, minute=minute)
                    start_iso = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    start_iso = dt.strftime("%d/%m/%Y")
                end_iso = None

    # 2) Intent detection
    if 'preciso' in msg_lower or (re.search(r'\b(coloque|colocar|adicione|adicionar|ponha|inclua|incluir|insira|acrescente|crie)\b', msg_lower) and ('tarefas' in msg_lower or 'tarefa' in msg_lower)):
        intent = 'new_task'
    elif re.search(r'\b(mostre|tenho|quais)\b', msg_lower) and ('tarefas' in msg_lower or 'tarefa' in msg_lower):
        intent = 'task_status'
    elif re.search(r'\b(terminei|já fiz|concluí|acabei|finalizei)\b', msg_lower):
        intent = 'task_conclusion'
    elif re.search(r'\b(quais|mostre)\b', msg_lower) and 'eventos' in msg_lower:
        intent = 'list_calendar'
    elif (re.search(r'\b(crie|adicione|novo)\b', msg_lower) and 'evento' in msg_lower) or re.search(r'\b(reunião.*às)\b', msg_lower):
        intent = 'create_calendar'
    elif re.search(r'\b(coloque|colocar|adicione|adicionar|ponha|inclua|incluir|insira|acrescente|crie)\b', msg_lower) and re.search(r'\blista\b', msg_lower):
        intent = 'create_list_item'
    elif re.search(r'\b(de)\b', msg_lower) and re.search(r'\blista\b', msg_lower):
        intent = 'list_user_list_items'
    else:
        intent = 'unrelated'

    # 3) Extract title
    title: Optional[str] = None
    if intent in ('new_task', 'task_conclusion', 'create_calendar'):
        pattern = r'"([^"]+)"'
        title = re.findall(pattern, text)[0] if re.findall(pattern, text) else None
    elif intent in ('create_list_item', 'list_user_list_items'):
        # tenta extrair o nome da lista após "lista de"
        match = re.search(r'lista de ([\wçãõáéíóúâêôàèìòùü\s]+)', msg_lower)
        if match:
            title = match.group(1).strip()

    # 4) Extract details for list item
    items = []
    if intent == 'create_list_item':
        items = extract_list_items(msg_lower)

    return {
        "message": text,
        "type": intent,
        "title": title or None,
        "start_date": start_iso,
        "end_date": end_iso,
        "priority": None,
        "details": None,
        "items": items
    }


def check_intents(user_message: str) -> List[str]:
    intents = []
    msg = user_message.lower()

    if re.search(r"\b(agendas?|eventos?|compromissos?|calendários?|reunião|reuniões|dia)\b", msg):
        intents.append("calendar")
    if re.search(r"\b(tarefas?|afazer|pendências?|atividades?|dia)\b", msg):
        intents.append("tasks")

    return intents