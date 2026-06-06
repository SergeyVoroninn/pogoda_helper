import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_core.tools import tool

embeddings = HuggingFaceEmbeddings(
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    cache_folder="./models/"
)

db = FAISS.load_local(
    'faiss_clothes_index',
    embeddings,
    allow_dangerous_deserialization=True
    )

@tool
def get_cloth_advise(weather_desc:str, sex: str) -> str:
    """
    Используй этот инструмент для рекомендаций как лучше одеться по погоде. 
    На входе: текстовое описание погоды, пол человека. 
    На выходе: рекомендации что надеть.
    """
    input = f'Для {sex} и погоды: {weather_desc}'
    result = db.similarity_search(input, k = 1)
    if result:
        return result[0].page_content
    else:
        return 'Не удалось найти в базе данных подходящих правил для такой погоды'

# if __name__ == '__main__':
#     test_query = 'На улице зима, -15 градусов'

#     result = get_cloth_advise.invoke({'weather_desc':test_query,'sex':'Male'})
#     print(result)