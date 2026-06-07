import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.weather_request import get_weather
from tools.retrival_clothes import get_cloth_advise
from tools.update_profile import update_profile
from langchain.messages import HumanMessage, ToolMessage, SystemMessage
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")



def run_agent(query:str,user_id:int) -> str:

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.getenv("GEMINI_API"),
        # openai_api_base = 'https://openrouter.ai/api/v1',
        # openai_api_key = API_KEY,
        temperature=0.3
    )

    tools = [get_weather,get_cloth_advise,update_profile]

    model_with_tools = model.bind_tools(tools = tools)

    system_promt = """
    Ты помощник стилист, и метеоассистент, твоя задача порекомендовать человеку что надеть в текущее время его городе,
    так же важно выделить пол человека,
    твои рекомендации должны соответствовать мужской и женской одежде,
    Чтобы узнать текущую погоду воспользуйся инструментом, но он выдаёт сырые данные,
    переведи выход в русский текст и округли градусы до целых значений перед обращением в базу данных.
    Текущий ID пользователя (user_id): {user_id}. 
    Если пользователь предоставил информацию о своём поле или имени или городе, 
    вызови инструмент для обновления профиля, обязательно передав этот user_id.
    Обязательно выдавай на выходе одежду для мужчин или для женщин если знаешь с кем говоришь, если нет, то для обоих полов
    """

    messages = [
        SystemMessage(content = system_promt),
        HumanMessage(query)
    ]

    for i in range(5):

        response = model_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        else:
            for iter_tool in response.tool_calls:
                
                tool_name = iter_tool['name']
                
                args = iter_tool['args']
                # print(f'using tool_name {tool_name} with args {args}')
                target_tool = next(t for t in tools if t.name == tool_name)

                result = target_tool.invoke(args)

                messages.append(ToolMessage(content=result,tool_call_id =iter_tool['id']))

        # print(messages)
    
      
    return response.text

def hello_chat() -> str:
    return """
Привет! Я секретная разработка для людей, непонимающих что надеть на улицу, буду помогать выбрать одежду 
Я умею обращатся к погодному апи, узная погодку в твоём городе и к собственной базе знаний.
Подскажи, как тебя зовут и где ты находишься, чтобы я мог проконсультировать тебя
    """

if __name__ == '__main__':
    
    assistant_name = 'Pogoda_helper: '
    user_name = 'You: '

    print(f'{assistant_name}{hello_chat()}')
    while True:
        print(f'{user_name}', end='')
        user_query = input()
        if user_query == 'exit' or user_query == 'выход' or user_query == 'quit':
            break
        try:
            output = run_agent(user_query)
            print(f'{assistant_name}{output}')
        except:
            print(f'{assistant_name}Ой что-то пошло не так!')
