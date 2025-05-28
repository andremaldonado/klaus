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
        return False


"""
Task creation tests
"""
def test_create_task_with_natural_date():
    msg = 'Preciso "revisar o relatório" amanhã às 14:00'
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert "revisar o relatório" in result["title"].lower()
    assert is_valid_date(result["start_date"])
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    expected_date = tomorrow.strftime("%d/%m/%Y %H:%M")
    assert result["start_date"] == expected_date

    msg = 'Insira, por favor, "Responder para o Lui sobre a formatação dos times com o novo EM" na minha lista de tarefas para amanhã às 15:00'
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert "responder para o lui sobre a formatação dos times com o novo em" in result["title"].lower()
    assert is_valid_date(result["start_date"])
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    expected_date = tomorrow.strftime("%d/%m/%Y %H:%M")
    assert result["start_date"] == expected_date

def test_create_task_without_date():
    msg = 'Crie esta tarefa: "testar o app"'
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert "testar o app" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

def test_create_task_without_title():
    msg = 'Coloque lavar a louça na minha lista de tarefas, por favor'
    result = interpret_user_message(msg)
    assert result["type"] == "new_task"
    assert result["title"] is None
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

    msg = "Quais tarefas tenho para hoje?"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

    msg = "Klaus, liste as tarefas que tenho para hoje"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

    msg = "Mostre minhas tarefas de hoje"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today

    msg = "O que tenho na minha lista de tarefas para hoje?"
    result = interpret_user_message(msg)
    assert result["type"] == "task_status"
    today = datetime.now().strftime("%d/%m/%Y")
    assert result["start_date"] == today


"""
Task completion tests
"""
def test_task_conclusion_statement():
    msg = 'Já terminei de "ler o livro"'
    result = interpret_user_message(msg)
    assert result["type"] == "task_conclusion"
    assert result["title"] is not None
    assert "ler o livro" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = 'Acabei meu "1:1 com o Rafa"'
    result = interpret_user_message(msg)
    assert result["type"] == "task_conclusion"
    assert result["title"] is not None
    assert "1:1 com o rafa" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = 'Finalizei a tarefa de "abrir a vaga para o time de lojas"'
    result = interpret_user_message(msg)
    assert result["type"] == "task_conclusion"
    assert result["title"] is not None
    assert "abrir a vaga para o time de lojas" in result["title"].lower()
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

"""
Event creation tests
"""
def test_create_event_with_range():
    msg = 'Crie este evento: "Reunião com equipe" das 10:00 às 11:00 no dia 10/10/2025'
    result = interpret_user_message(msg)
    assert result["type"] == "create_calendar"
    assert "reunião com equipe" in result["title"].lower()
    assert result["start_date"] == "10/10/2025 10:00"
    assert result["end_date"] == "10/10/2025 11:00"

    msg = '"Reunião com equipe" das 20:00 às 21:00 no dia 11/10/2025'
    result = interpret_user_message(msg)
    assert result["type"] == "create_calendar"
    assert "reunião com equipe" in result["title"].lower()
    assert result["start_date"] == "11/10/2025 20:00"
    assert result["end_date"] == "11/10/2025 21:00"


"""
List list items tests
"""

def test_list_user_list_items():
    msg = "O que tenho na minha lista de compras?"
    result = interpret_user_message(msg)
    assert result["type"] == "list_user_list_items"
    assert result["title"] == "compras"

    msg = "Como está minha lista de projetos do trabalho?"
    result = interpret_user_message(msg)
    assert result["type"] == "list_user_list_items"
    assert result["title"] == "projetos do trabalho"

    msg = "Klaus me liste o que tenho na minha lista de compras de supermercado"
    result = interpret_user_message(msg)
    assert result["type"] == "list_user_list_items"
    assert result["title"] == "compras de supermercado"


"""
Create list items tests
"""

def test_create_list_items():
    msg = "Adicione \"pão\" na minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["pão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Adicionar \"whey protein\" na lista de compras do mercado livre"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras do mercado livre"
    assert result["items"] == ["whey protein"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Coloque \"banana\" e \"batata\" na lista de compras da feira"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras da feira"
    assert result["items"] == ["banana", "batata"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Ahhh perfeito, então coloque \"banana\" na minha lista de compras, por favor."
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["banana"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Acrescente \"banana\" na minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["banana"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Klaus, coloca \"ovo\" na minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["ovo"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

def test_create_list_items_with_different_quotes():
    msg = 'Klaus, adicione “requeijão” na minha lista de compras'
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "Adicionar 'whey protein' na lista de compras do mercado livre"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras do mercado livre"
    assert result["items"] == ["whey protein"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = 'Klaus, adicione \'requeijão\' na minha lista de compras'
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = 'Klaus, adicione ‘requeijão’ na minha lista de compras'
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

def test_create_list_items_without_quotes():
    msg = "Acrescente banana na minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "create_list_item"
    assert result["title"] == "compras"
    assert result["items"] == []
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

def test_remove_list_item():
    msg = "klaus, remova o item \"requeijão\" da minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "remove_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "klaus, exclua o item \"requeijão\" e 'batata' da minha lista de compras"
    result = interpret_user_message(msg)
    assert result["type"] == "remove_list_item"
    assert result["title"] == "compras"
    assert result["items"] == ["requeijão","batata"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "apagar \"requeijão\" da lista do mercado"
    result = interpret_user_message(msg)
    assert result["type"] == "remove_list_item"
    assert result["title"] == "mercado"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None

    msg = "apagar \"requeijão\" da lista da festa da firma"
    result = interpret_user_message(msg)
    assert result["type"] == "remove_list_item"
    assert result["title"] == "festa da firma"
    assert result["items"] == ["requeijão"]
    assert result["priority"] is None
    assert result["start_date"] is None
    assert result["end_date"] is None


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