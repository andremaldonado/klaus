import json
import os
import pytz
import re

from dateparser import parse as dp_parse
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional


# Constants
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))
TODAY_DATE = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
BASIC_INSTRUCTIONS = [
    "Você é Klaus, um assistente pessoal pronto para ajudar em qualquer tarefa que o usuário solicitar.",
    "Você usa um complexo sistema de apoio para te suportar nas operações que o usuário solicitar, como agenda, tarefas e gerenciamento de listas.",
    "Sua missão é manter uma conversa agradável e útil com o usuário, sempre com um tom respeitoso e conciso.",
    "Você pode responder perguntas, oferecer sugestões, criar tarefas, organizar eventos, manusear listas, e muito mais.",
    "Considere que sua memória é específica para o contexto do que o usuário está pedindo.",
    "Você usa o histórico de conversa e memórias relevantes para responder de forma natural. ",
    "Não peça para o usuário repetir informações já dadas.", 
    f"Hoje é {TODAY_DATE}.",
    "=== Instruções de Formatação da resposta ===",
    "- Use texto simples. Você pode usar quebras de linha para separar tópicos.",
    "- Evite formatação em Markdown.",
    "- Use emojis quando entender ser necessário."
]
INSERTION_KEYWORDS = r'\b(?:coloque|coloca|colocar|adicione|adicionar|ponha|inclua|incluir|insira|acrescente|crie)\b'
SHOW_KEYWORDS = r'\b(?:mostre|tenho|quais)\b'
FINISH_KEYWORDS = r'\b(?:terminei|já fiz|concluí|acabei|finalizei)\b'
CREATE_KEYWORDS = r'\b(crie|adicione|novo)\b'
REMOVAL_KEYWORDS = r'\b(remova|remove|remover|exclua|excluir|delete|deletar|apague|apagar|retire|retirar|tire|tira|tirar)\b'
BETWEEN_QUOTES = r'["“”‘’\'«»]([^"“”‘’\'\'«»]+)["“”‘’\'«»]'


# AI Configuration
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _extract_date(msg_lower):
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
    return start_iso,end_iso


def _extract_list_items(text: str) -> List[str]:
    pattern = BETWEEN_QUOTES
    return re.findall(pattern, text)


def check_intents(user_message: str) -> List[str]:
    intents = []
    msg = user_message.lower()

    if re.search(r"\b(agendas?|eventos?|compromissos?|calendários?|reunião|reuniões|dia)\b", msg):
        intents.append("calendar")
    if re.search(r"\b(tarefas?|afazer|pendências?|atividades?|dia)\b", msg):
        intents.append("tasks")

    return intents


def chat(message: str, context: list[dict[str, str]]) -> str:

    ai_prompt_system_context = []
    for msg in context:
        ai_prompt_system_context.append(f"{msg["content"]}")
    for item in BASIC_INSTRUCTIONS:
        ai_prompt_system_context.append(item)

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=message,
        config=genai.types.GenerateContentConfig(
            system_instruction=ai_prompt_system_context,
            temperature=2.0
        )
    )
    return response.text


def generate_tasks_suggestion(tasks: str, events: str, user_context: str) -> str:
    # Generates a suggestion using ChatGPT based on the provided tasks and user context.
    today_date = datetime.now(TIMEZONE).strftime("%d/%m/%Y %H:%M")
    
    ai_prompt_system_context = []
    for item in BASIC_INSTRUCTIONS:
        ai_prompt_system_context.append(item)
    ai_prompt_system_context.append("=== Instruções de Resposta ===")
    ai_prompt_system_context.append(f"Abaixo estão as tarefas do usuário: {tasks}")
    ai_prompt_system_context.append(f"Abaixo está a agenda do usuário: {events}")
    ai_prompt_system_context.append("Responda à solicitação do usuário considerando o contexto do usuário e as tarefas listadas.")
    ai_prompt_system_context.append("Note que podem existir tarefas e eventos para outros dias ou que já foram finalizados.")
    ai_prompt_system_context.append("Considere isso para responder ao usuário de acordo com a solicitação dele.")

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
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
    
    # 1) Extract date information
    start_iso, end_iso = _extract_date(msg_lower)

    # 2) Intent detection
    if 'preciso' in msg_lower or (re.search(INSERTION_KEYWORDS, msg_lower) and ('tarefas' in msg_lower or 'tarefa' in msg_lower)):
        intent = 'new_task'
    elif re.search(SHOW_KEYWORDS, msg_lower) and ('tarefas' in msg_lower or 'tarefa' in msg_lower):
        intent = 'task_status'
    elif re.search(FINISH_KEYWORDS, msg_lower):
        intent = 'task_conclusion'
    elif re.search(SHOW_KEYWORDS, msg_lower) and 'eventos' in msg_lower:
        intent = 'list_calendar'
    elif (re.search(CREATE_KEYWORDS, msg_lower) and 'evento' in msg_lower) or re.search(r'\b(reunião.*às)\b', msg_lower):
        intent = 'create_calendar'
    elif re.search(INSERTION_KEYWORDS, msg_lower) and re.search(r'\blista\b', msg_lower):
        intent = 'create_list_item'
    elif re.search(REMOVAL_KEYWORDS, msg_lower) and re.search(r'\blista\b', msg_lower):
        intent = 'remove_list_item'
    elif re.search(r'\b(de)\b', msg_lower) and re.search(r'\blista\b', msg_lower):
        intent = 'list_user_list_items'
    else:
        intent = 'unrelated'

    # 3) Extract title
    title: Optional[str] = None
    if intent in ('new_task', 'task_conclusion', 'create_calendar'):
        pattern = BETWEEN_QUOTES
        title = re.findall(pattern, text)[0] if re.findall(pattern, text) else None
    elif intent in ('create_list_item', 'list_user_list_items', 'remove_list_item'):
        # tenta extrair o nome da lista após "lista de"
        match = re.search(r'\blista\b (?:\bde\b|\bdo\b|\bda\b) ([\wçãõáéíóúâêôàèìòùü\s]+)', msg_lower)
        if match:
            title = match.group(1).strip()

    # 4) Extract details for list item
    items = []
    if intent in ('create_list_item','remove_list_item'):
        items = _extract_list_items(msg_lower)

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