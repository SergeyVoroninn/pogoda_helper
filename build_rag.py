import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def build_vector_db():
    
    with open('clothes_rules.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,
        chunk_overlap = 150,
        separators='\n'
    )
    chunks = text_splitter.split_text(text=text)
    print(f'Текст успешно нарезан на {len(chunks)}')

    embeddings = HuggingFaceEmbeddings(
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_folder="./models/"
    )
    db = FAISS.from_texts(chunks,embeddings)
    
    db.save_local('faiss_clothes_index')

if __name__ == "__main__":
    build_vector_db()