from langchain_core.tools import tool
from database import upsert_user_profile
@tool
def update_profile(user_id: int, name: str = None, sex: str = None, city: str = None):
    """
    Используй этот инструмент, чтобы добавить в базу данных информацию о пользователе. 
    Используй его если пользователь предоставил личную информацию.
    
    Args:
        user_id (int): уникальный номер пользователя в телеграмме,
        name (str): Имя пользователя (например 'Андрей', 'Серега'),
        sex (str): Пол пользователя. Если не знаешь можно спросить,
        city (str): Название города (например, 'Новосибирск', 'Москва', 'Лондон').

    Если нет некоторой информации, можно оставить поля пустыми  
    """
    
    upsert_user_profile(user_id,name,sex,city)

    output = f'Базы данных обновлены, {user_id}, {name}, {sex}, {city}'
    
    return output