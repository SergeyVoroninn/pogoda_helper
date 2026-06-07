import asyncio
from aiogram import Bot, Dispatcher, types

import logging
import dotenv
import os
from aiogram.filters.command import Command
from agent import run_agent, hello_chat
from database import init_database, add_dialog_message, upsert_user_profile

dotenv.load_dotenv()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Бот
BOT_TOKEN = os.getenv('TELEGRAM_API')
# Диспетчер
dp = Dispatcher()
bot = Bot(token = BOT_TOKEN)

# Хэндлер на команду старт
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await asyncio.to_thread(upsert_user_profile, message.from_user.id ) ###
    await message.answer(hello_chat())

@dp.message()
async def agent_call(message: types.Message):
    await asyncio.to_thread(add_dialog_message, message.from_user.id,'user', message.text)

    answer = await asyncio.to_thread(run_agent, message.text, message.from_user.id)

    await message.answer(answer, parse_mode='Markdown')

    await asyncio.to_thread(add_dialog_message, message.from_user.id,'assistant', answer) ####

async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":

    init_database()
    asyncio.run(main())