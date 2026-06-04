import requests
from langchain_core.tools import tool

@tool
def get_weather(city=None):
    """ 
    Используй этот инструмент, чтобы узнать текущую погоду в конкретном городе. На вход принимает название города.
    На выходе предоставляется информация о городе, температуре, влажности, вероятносте осадков, вероятности снега, скорости ветра
    """
    API_KEY = '8a95550fe5004d8090b54613260406'
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

    output = f'В городе {loc_name} сейчас {cond}, температура: {temp_c} C, влажность: {humidity}, вероятность осадков: {chance_of_rain}, вероятность снега: {chance_of_snow}, скорость ветра: {wind_mph}'
    
    return output

print(get_weather.name)          
print(get_weather.description)  
print(get_weather.invoke('Novosibirsk'))