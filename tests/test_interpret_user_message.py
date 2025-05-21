import pytest
from datetime import datetime, timedelta

from ai_assistant import interpret_user_message


"""
Helpers
"""
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        return True
    except Exception as e:
        print(f"❌ [ERROR] {e}: {date_str}")
        return False


"""
Task creation tests
"""
def test_create_task_with_natural_date():
    msg = "Preciso revisar o relatório amanhã às 14:00"
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert "revisar o relatório" in result["title"].lower()
    assert is_valid_date(result["start_date"])
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    expected_date = tomorrow.strftime("%d/%m/%Y %H:%M")
    assert result["start_date"] == expected_date

def test_create_task_without_date():
    msg = "Crie esta tarefa: testar o app"
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert "testar o app" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None


"""
Task status tests
"""
def test_task_status_question():
    msg = "Tenho tarefas para hoje?"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

def test_task_status_question_variation_1():
    msg = "Quais tarefas tenho para hoje?"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

def test_task_status_question_variation_2():
    msg = "Klaus, liste as tarefas que tenho para hoje"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

def test_task_status_question_variation_2():
    msg = "Mostre minhas tarefas de hoje"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

def test_task_status_question_variation_2():
    msg = "Quais minhas tarefas de hoje"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today


"""
Task completion tests
"""
def test_task_conclusion_statement():
    msg = "Já terminei de ler o livro"
    result = interpret_user_message(msg)
    assert result["type"] == "task_conclusion"
    assert result["title"] is not None
    assert "ler o livro" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

def test_task_conclusion_statement():
    msg = "Acabei meu 1:1 com o Rafa"
    result = interpret_user_message(msg)
    assert result["type"] == "task_conclusion"
    assert result["title"] is not None
    assert "1:1 com o rafa" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

"""
Event creation tests
"""
def test_create_event_with_range():
    msg = "Crie este evento: Reunião com equipe das 10:00 às 11:00 no dia 10/10/2025"
    result = interpret_user_message(msg)
    assert result["type"] == "create_calendar"
    assert "reunião com equipe" in result["title"].lower()
    assert result["start_date"] == "10/10/2025 10:00"
    assert result["end_date"] == "10/10/2025 11:00"


def test_create_event_with_range_variation_1():
    msg = "Reunião com equipe das 20:00 às 21:00 no dia 11/10/2025"
    result = interpret_user_message(msg)
    assert result["type"] == "create_calendar"
    assert "reunião com equipe" in result["title"].lower()
    assert result["start_date"] == "11/10/2025 20:00"
    assert result["end_date"] == "11/10/2025 21:00"

"""
Unrelated tests
"""
def test_unrelated_message():
    msg = "Você gosta de pizza?"
    result = interpret_user_message(msg)
    assert result["type"] == "unrelated"
    assert result["title"] is None
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None