import requests
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
@tool
def get_weather(city: str) -> str:
    """
    Используй этот инструмент, чтобы узнать текущую погоду в конкретном городе.
    
    Args:
        city (str): Название города СТРОГО на английском языке (например, 'Novosibirsk', 'Moscow', 'London').   
    """
    load_dotenv()
    API_KEY = os.getenv("WEATHER_API_KEY")
    url = f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=yes'
    response = requests.get(url=url)

    if response.status_code != 200:
        print(f'error status_code {response.status_code}')
        return 'Error during request'
    # print(response._content)
    dct = response.json()
    chance_of_rain = dct['current']['chance_of_rain']
    chance_of_snow = dct['current']['chance_of_snow']
    wind_mph = dct['current']['wind_mph']
    temp_c = dct['current']['temp_c']
    cond = dct['current']['condition']['text']
    loc_name = dct['location']['name']
    humidity = dct['current']['humidity']

    output = f'В городе {loc_name} сейчас {cond}, температура: {temp_c} C, влажность: {humidity} %, вероятность осадков: {chance_of_rain}%, вероятность снега: {chance_of_snow} %, скорость ветра: {wind_mph} м/с'
    
    return output
