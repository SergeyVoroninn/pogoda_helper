import asyncio
from aiogram import Bot, Dispatcher, types

import logging
import dotenv
import os
from aiogram.filters.command import Command

# Добавь импорт самого graph из файла agent, чтобы было что компилировать
from agent import graph, hello_chat
from database import init_database, upsert_user_profile

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# Исправлен импорт HumanMessage из правильного пакета langchain_core
from langchain_core.messages import HumanMessage

dotenv.load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Бот
BOT_TOKEN = os.getenv('TELEGRAM_API')
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


# Хэндлер на команду старт
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await asyncio.to_thread(upsert_user_profile, message.from_user.id)
    await message.answer(hello_chat())


# Хэндлер на любое сообщение
@dp.message()
async def agent_call(message: types.Message, app):  # <-- Принимаем скомпилированный граф прямо в аргументы!
    
    # Статусное сообщение
    status_message = await message.answer('Отправляю запрос в далёкие уголки интернетов..')

    # Конфигурация с thread_id
    config = {"configurable": {"thread_id": str(message.from_user.id)}}
    
    # Исправили: user_id передаем как int, так как в твоем MyGraphState заявлен int
    initial_input = {
        "user_id": message.from_user.id,
        "messages": [HumanMessage(content=message.text)]
    }
    
    try:
        # Показываем плашку "печатает..." для красоты
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Запуск агента
        result = await app.ainvoke(initial_input, config=config)
        
        # Удаление статуса
        await status_message.delete()
        
        # Ответ агента. 
        bot_answer = result["messages"][-1].content
        await message.answer(bot_answer, parse_mode=None)

    except Exception as e:
        # Удаление статуса в случае падения
        try:
            await status_message.delete()
        except Exception:
            pass
            
        # Проверяем, есть ли у ошибки атрибут ответа от сервера
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            
            if status_code == 429:
                await message.answer("Извини, но бесплатные буквы от гугла на сегодня закончились (Кончилась квота)")
                return
            elif status_code == 503:
                await message.answer("У гуглов сейчас перегруз, попробуй позже (503)")
                return
            else:
                await message.answer(f"ААшибка, статус код {status_code}, попробуйте позже или обратитесь к @stereogad в тг")
                return
        
        # Если упала какая-то другая логика ноды
        print(f"Ошибка выполнения графа: {e}")
        await message.answer("Что-то пошло не так внутри подбора одежды. Попробуй еще раз!")


async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Открываем асинхронное соединение с бд чекпоинтера
    async with AsyncSqliteSaver.from_conn_string("pogoda_helper.db") as memory_db:
        
        print("--- Компиляция графа с чекпоинтером ---")
        # 1. Сначала компилируем граф внутри контекста базы данных
        compiled_app = graph.compile(checkpointer=memory_db)
        
        # 2. Передаем скомпилированное приложение в workflow_data диспетчера.
        # Теперь aiogram автоматически прокинет этот граф во все хэндлеры, 
        # где в аргументах написано `, app`!
        dp.workflow_data["app"] = compiled_app
        
        print("--- Запуск пуллинга ТГ бота ---")
        # 3. И только теперь запускаем бесконечный цикл пуллинга
        await dp.start_polling(bot)


if __name__ == "__main__":
    init_database()
    asyncio.run(main())