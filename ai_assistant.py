import os
import json
from datetime import datetime
from google import genai
from habitica_api import format_tasks

def generate_chatgpt_suggestion(tasks, user_context):
    """
    Generates a suggestion using ChatGPT based on the provided tasks and user context.
    """
    tasks_text = format_tasks(tasks)
    today_date = datetime.now().strftime("%d/%m/%Y")
    
    ai_prompt_system_context = (
        "Você é Klaus, um assistente pessoal calmo, educado e objetivo. "
        "Sua missão é analisar as tarefas do usuário e fornecer sugestões práticas. "
        "Use sempre um tom respeitoso, porém conciso.\n\n"
        "=== Instruções de Formatação para Telegram ===\n"
        "- Use texto simples. Você pode usar quebras de linha para separar tópicos.\n"
        "- Evite formatação em Markdown.\n"
        "- Use emojis para indicar prioridade e status.\n\n"
        f"Hoje é {today_date}. Abaixo estão as tarefas do usuário, separadas por ponto e vírgula:\n"
        f"{tasks_text}\n\n"
        "=== Exemplo de Resposta ===\n"
        "Bom dia! Você tem algumas tarefas pendentes hoje. "
        "Sugiro começar pelas tarefas com datas mais próximas ou já vencidas. "
        "Em seguida, se tiver tempo, avance para as demais. "
        "Evite deixar tarefas se acumularem por vários dias.\n\n"
        "Por favor, priorize tarefas urgentes ou de maior impacto e mantenha um tom positivo. "
        "Responda considerando o contexto do usuário e as tarefas listadas."
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_context,
        config=genai.types.GenerateContentConfig(
            system_instruction=ai_prompt_system_context,
            temperature=0.5
        )
    )

    return response.text

def interpret_user_message(user_message):
    """
    Interprets the user message to determine whether it refers to a new task creation,
    a request for task status, or is unrelated. It returns a structured JSON with
    the following fields:
    {
      "message": [original user message],
      "type": ["new_task" | "task_status" | "unrelated"],
      "task": [brief task title or null],
      "date": [date mentioned like "hoje", "amanhã", or null],
      "priority": ["low" | "medium" | "high" | null]
    }
    """
    
    ai_prompt_engineering_prompt = (
        """Aja como um especialista em interpretação de linguagem natural e extração de informações a partir de mensagens de texto. Sua tarefa é classificar a intenção da mensagem do usuário e extrair informações relevantes.
        INSTRUÇÃO

        Você receberá uma mensagem de usuário. Sua tarefa é determinar se a mensagem:

        - Refere-se à criação de uma nova tarefa.
        - Solicita o status de tarefas existentes.
        - Solicita a conclusão de uma tarefa.
        - Não está relacionada a nenhuma das anteriores.

        Você DEVE extrair os seguintes campos e retorná-los em JSON no seguinte formato:

        {
        "message": [mensagem original do usuário],
        "type": ["new_task" | "task_status" | "task_conclusion" | "unrelated"],
        "task": [título resumido da tarefa ou null],
        "date": [data mencionada como "hoje", "amanhã" ou null],
        "priority": ["low" | "medium" | "high" | null]
        }

        É imprescindível que esse retorno não tenha nenhuma formatação, nem mesmo algo como ```json.

        Seja rigoroso em sua classificação. Se uma mensagem for ambígua ou não se referir claramente a uma tarefa ou ao seu status, classifique-a como "unrelated".

        Ao extrair a prioridade, considere não apenas palavras‑chave explícitas, mas também a urgência implícita no tom. Por exemplo:

        - "preciso muito", "urgente", "o quanto antes" → high  
        - "se possível", "talvez", "mais tarde" → low

        Mantenha o texto original em português nos campos "message" e "date".

        EXEMPLOS

        Usuário: "Preciso ir na academia hoje"  
        Saída: { "message": "Preciso ir na academia hoje", "type": "new_task", "task": "ir na academia", "date": "hoje", "priority": null }

        Usuário: "Quais tarefas minhas estão atrasadas?"  
        Saída: { "message": "Quais tarefas minhas estão atrasadas?", "type": "task_status", "task": null, "date": null, "priority": null }

        Usuário: "Tenho tarefas para hoje? Quais?"  
        Saída: { "message": "Tenho tarefas para hoje? Quais?", "type": "task_status", "task": null, "date": "hoje", "priority": null }

        Usuário: "A pizza chegou"  
        Saída: { "message": "A pizza chegou", "type": "unrelated", "task": null, "date": null, "priority": null }

        Usuário: "Terminei de ler o livro"
        Saída: { "message": "Terminei de ler o livro", "type": "task_conclusion", "task": "ler o livro", "date": null, "priority": null }

        Usuário: "Já fiz a lição"
        Saída: { "message": "Já fiz a lição", "type": "task_conclusion", "task": "lição", "date": null, "priority": null }

        FIM

        Agora, processe a seguinte mensagem de acordo com as instruções."""
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
            "task": None,
            "date": None,
            "priority": None
        }
    return result