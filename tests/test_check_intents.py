from src.klaus.handlers.ai_assistant import check_intents


def test_check_intents_with_calendar_keywords():
    assert "calendar" in check_intents("Tenho um evento amanhã")
    assert "calendar" in check_intents("Qual é o meu compromisso?")
    assert "calendar" in check_intents("Adicione ao meu calendário")
    assert "calendar" in check_intents("Tenho uma reunião às 10h")
    assert "calendar" in check_intents("O que tenho no dia 10/10/2025?")
    assert "calendar" in check_intents("Quais eventos estão agendados?")
    assert "calendar" in check_intents("Quais compromissos tenho para hoje?")
    assert "calendar" in check_intents("Quais reuniões tenho para hoje?")


def test_check_intents_with_tasks_keywords():
    assert "tasks" in check_intents("Quais tarefas tenho para hoje?")
    assert "tasks" in check_intents("Liste minhas pendências")
    assert "tasks" in check_intents("Qual atividade está pendente?")
    assert "tasks" in check_intents("Tenho algum afazer?")
    assert "tasks" in check_intents("O que preciso fazer no dia 12/12/2024?")


def test_check_intents_with_both_keywords():
    result = check_intents("Tenho uma reunião e uma tarefa para hoje")
    assert "calendar" in result
    assert "tasks" in result


def test_check_intents_with_mispelled_keywords():
    assert check_intents("Quais tarefass tenho para hoje?") == []
    assert check_intents("Liste minhas pendênciass") == []
    assert check_intents("Qual atividadi está pendente?") == []
    assert check_intents("Tenho algum afaze?") == []
    assert check_intents("Tenho um eventoss amanhã") == []
    assert check_intents("Qual é o meu compromissoss?") == []
    

def test_check_intents_with_no_keywords():
    assert check_intents("Você gosta de pizza?") == []


def test_check_intents_case_insensitivity():
    assert "calendar" in check_intents("AGENDA para amanhã")
    assert "tasks" in check_intents("TAREFA urgente")