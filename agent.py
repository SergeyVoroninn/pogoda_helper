import os
from dotenv import load_dotenv

from tools.weather_request import get_weather
from tools.retrival_clothes import get_cloth_advise
from tools.update_profile import update_profile

from database import get_profile

import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

load_dotenv()

# API_KEY = os.getenv("OPENROUTER_API_KEY")

# УЗЕЛ ГРАФА (обновляемый по прохождению графа)
class MyGraphState(TypedDict):

    user_id: int # Твой порядковый
    sex: str  # Секс друг
    city: str  # Город
    name: str  # Твоё имя 

    weather_output: str # выхолоп из weather API
    cloth_output:str # выхлоп из RAG с одеждой
    messages: Annotated[list, add_messages] # все сообщения


# def check_profile_node(state: MyGraphState):
#     print('--- [NODE] ПРОВЕРКА ПРОФИЛЯ ---') # МОК ПРОВЕРКА, СДЕЛАЮ В БУДУЩЕМ

async def cloth_node(state: MyGraphState):
    print("--- [NODE] ПОИСК по ВЕКТОРКЕ   ---")
    weather_output = state.get("weather_output")
    sex = state.get("sex")

    if weather_output is not None and sex is not None:
        result = await get_cloth_advise.ainvoke({"sex": sex, 'weather_desc':weather_output})
    else:
        result = 'NO DATA'

    return {
        "cloth_output": result,
    }

async def weather_node(state: MyGraphState):
    print("--- [NODE] Обращение к API с погодой ---")
    city = state.get('city')

    if city is not None:
        result =  await get_weather.ainvoke({"city": city})
    else:
        result = 'NO DATA'

    return {
        "weather_output": result,
    }


def load_profile_node(state: MyGraphState):
    print("--- [NODE] Загрузка профиля ---")
    user_id = state["user_id"]

    # поход в БД:
    db_profile = get_profile(user_id)
    
    # Возвращаем словарь — обновляем глобальный State графа
    return {
        "name": db_profile.get("name"),
        "city": db_profile.get("city"),
        "sex": db_profile.get("sex")
    }

def decision_node(state: MyGraphState):
    print('--- [NODE] Решение о перезагрузке графа ---')

    if isinstance(state["messages"][-1], ToolMessage):
        return "load_profile_node"
    
    return "END"

async def run_agent_node(state: MyGraphState) -> str:
    user_id = state.get('user_id')
    sex = state.get('sex')
    city = state.get('city')
    weather_output = state.get('weather_output')
    cloth_output = state.get('cloth_output')
    query = state.get('messages')[-1]

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.getenv("GEMINI_API"),
        # openai_api_base = 'https://openrouter.ai/api/v1',
        # openai_api_key = API_KEY,
        temperature=0.3
    )

    tools = [update_profile]

    model_with_tools = model.bind_tools(tools = tools)

    system_promt = f"""
    Ты помощник стилист, и метеоассистент, твоя задача порекомендовать человеку что надеть в текущее время его городе,
    так же важно выделить пол человека,
    твои рекомендации должны соответствовать мужской и женской одежде,
    Текущий ID пользователя (user_id): {user_id}
    Пол пользователя: {sex}
    Город пользователя: {city}
    Погода в городе: {weather_output}
    Рекомендации одежды по векторной базе данных: {cloth_output}

    Если пользователь предоставил информацию о своём поле или имени или городе, 
    вызови инструмент для обновления профиля, обязательно передав на входе user_id, name, city, sex.

    Обязательно выдавай на выходе одежду для мужчин или для женщин если знаешь с кем говоришь, если нет, то для обоих полов
    Не нужно уведомлять пользователя о записи в базу данных информации, это внутренние процессы
    """

    messages_to_model = [SystemMessage(content = system_promt)] + state['messages']
    print('gemini start')
    response = await model_with_tools.ainvoke(messages_to_model)
    print('gemini finish')
    tool_result = None
    if response.tool_calls:
        for iter_tool in response.tool_calls:
            
            tool_name = iter_tool['name']
            
            args = iter_tool['args']

            target_tool = next(t for t in tools if t.name == tool_name)

            tool_result = await target_tool.ainvoke(args)

            tool_message = ToolMessage(content=str(tool_result), tool_call_id=response.tool_calls[0]['id'])
    
        return {"messages": [response, tool_message]}


    return {"messages": [AIMessage(content=response.text)]}

def hello_chat() -> str:
    return """
Привет! Я секретная разработка для людей, непонимающих что надеть на улицу, буду помогать выбрать одежду 
Я умею обращатся к погодному апи, узная погодку в твоём городе и к собственной базе знаний.
Подскажи, как тебя зовут и где ты находишься, чтобы я мог проконсультировать тебя
    """


graph = StateGraph(MyGraphState)

graph.add_node('load_profile', load_profile_node)
# graph.add_node('check_profile', check_profile_node)
graph.add_node('weather_request', weather_node)
graph.add_node('vector_db_find', cloth_node)
graph.add_node('run_agent', run_agent_node)

graph.set_entry_point('load_profile')

# Ветвь инструментов и ИИ
graph.add_edge('load_profile','weather_request')
# graph.add_edge('check_profile','weather_request')
graph.add_edge('weather_request','vector_db_find')
graph.add_edge('vector_db_find','run_agent')
# graph.add_edge('run_agent', 'restart_cond_edge')

# Условный переход вешается ПРЯМО на выход из ноды 'run_agent'
graph.add_conditional_edges(
    "run_agent",         # Откуда выходим
    decision_node,       # Функция-судья (твоя decision_node)
    {
        "load_profile_node": "load_profile",  # Если вернула строку "load_profile_node" -> идем в начало
        "END": END                            # Если вернула "END" -> закончить граф
    }
)


async def test():
    # 1. Открываем асинтекстный менеджер базы данных памяти
    async with AsyncSqliteSaver.from_conn_string("pogoda_helper.db") as memory_db:
        
        # 2. Компилируем граф ПРЯМО ТУТ, внутри контекста
        app = graph.compile(checkpointer=memory_db)
        
        # Конфигурация с thread_id (без неё чекпоинтер выдаст ошибку при вызове!)
        config = {"configurable": {"thread_id": "33335"}}
        
        initial_input = {
            "user_id": 33335,
            "messages": [HumanMessage(content="Привет! Что мне сегодня надеть? Меня зовут Максим, я из Краснодара")]
        }
        
        # 3. Запускаем конвейер, передавая config
        result = await app.ainvoke(initial_input, config=config)
        
        # Печатаем ответ
        print("\nОтвет бота в ТГ:", result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(test()) 

