import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import sqlite3
import aiofiles


API_TOKEN = 'TOKEN'


ADMIN_ID = 


CHAT_ID_FILE = 'config.txt'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def load_chat_ids():
    try:
        with open(CHAT_ID_FILE, 'r') as f:
            chat_ids = f.readlines()
        chat_ids = [line.strip() for line in chat_ids if line.strip()]
        logger.info(f"Загружено CHAT_ID: {chat_ids}")
        return chat_ids
    except Exception as e:
        logger.error(f"Ошибка при загрузке CHAT_IDs: {e}")
        return []


async def save_chat_id(chat_id):
    try:
        async with aiofiles.open(CHAT_ID_FILE, 'a') as f:
            await f.write(f"{chat_id}\n")
        logger.info(f"CHAT_ID {chat_id} успешно сохранен.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении CHAT_ID: {e}")


async def save_chat_ids(chat_ids):
    try:
        async with aiofiles.open(CHAT_ID_FILE, 'w') as f: 
            for chat_id in chat_ids:
                await f.write(f"{chat_id}\n")
        logger.info("CHAT_IDs успешно сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении CHAT_IDs: {e}")


async def delete_chat_id(chat_id):
    global CHAT_IDS
    chat_ids = load_chat_ids()

    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        await save_chat_ids(chat_ids)

        delete_chat_id_from_db(chat_id)

def delete_chat_id_from_db(chat_id):
    try:
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()
        logger.info(f"CHAT_ID {chat_id} успешно удален из базы данных.")
    except Exception as e:
        logger.error(f"Ошибка при удалении CHAT_ID {chat_id} из базы данных: {e}")

@dp.callback_query_handler(lambda c: c.data == 'delete_chat_id')
async def delete_chat(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == ADMIN_ID:
        global CHAT_IDS
        chat_ids = load_chat_ids()
        
        if chat_ids:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for chat_id in chat_ids:
                try:
                    chat = await bot.get_chat(chat_id) 
                    chat_name = chat.username if chat.username else chat.title  
                    
                    button = InlineKeyboardButton(f"Удалить канал {chat_name}", callback_data=f'delete_{chat_id}')
                    keyboard.add(button)
                except Exception as e:
                    logger.error(f"Ошибка при получении данных о чате {chat_id}: {e}")
                    continue

            await bot.send_message(callback_query.from_user.id, "Выберите канал для удаления:", reply_markup=keyboard)
        else:
            await bot.send_message(callback_query.from_user.id, "Нет доступных каналов для удаления.")
    else:
        await bot.send_message(callback_query.from_user.id, "У вас нет прав для удаления CHAT_ID.")
    
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def delete_chat(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == ADMIN_ID:
        chat_id = callback_query.data.split('_')[1] 
        
        await delete_chat_id(chat_id)

        global CHAT_IDS
        CHAT_IDS = load_chat_ids() 
        
        await bot.send_message(callback_query.from_user.id, f"Канал с ID {chat_id} был успешно удален.")

        await bot.answer_callback_query(callback_query.id)
    else:
        await bot.send_message(callback_query.from_user.id, "У вас нет прав для удаления канала.")

CHAT_IDS = load_chat_ids()

if not CHAT_IDS:
    logger.error("Нет сохранённых CHAT_ID в файле!")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    set_chat_button = InlineKeyboardButton("Добавить новый канал по @username", callback_data='set_chat_id')
    delete_chat_button = InlineKeyboardButton("Удалить канал", callback_data='delete_chat_id')

    keyboard.add(set_chat_button, delete_chat_button)
    
    await message.answer(f"Привет, вы админ!", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'set_chat_id')
async def set_chat_id(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        text="Пожалуйста, отправьте @username группы.",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None  
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(lambda message: message.text.startswith('@'))
async def set_chat_id_by_username(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            group_username = message.text.strip()

            chat = await bot.get_chat(group_username)
            new_chat_id = chat.id

            await save_chat_id(new_chat_id)
            global CHAT_IDS
            CHAT_IDS = load_chat_ids() 

            keyboard = InlineKeyboardMarkup(row_width=1)
            back_button = InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
            keyboard.add(back_button)

            await message.answer(f"CHAT_ID успешно добавлен: {new_chat_id} для группы {group_username}", reply_markup=keyboard)
        except Exception as e:
            keyboard = InlineKeyboardMarkup(row_width=1)
            back_button = InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')
            keyboard.add(back_button)
            await message.answer(f"Ошибка при получении CHAT_ID: {e}", reply_markup=keyboard)
    else:
        await message.answer("У вас нет прав для изменения CHAT_ID.")


@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def back_to_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)

    set_chat_button = InlineKeyboardButton("Добавить новый канал по @username", callback_data='set_chat_id')
    delete_chat_button = InlineKeyboardButton("Удалить канал", callback_data='delete_chat_id')

    keyboard.add(set_chat_button, delete_chat_button)

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Привет, вы админ!",
        reply_markup=keyboard
    )

conn = sqlite3.connect('messages.db') 
cursor = conn.cursor()

cursor.execute(''' 
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    timestamp TEXT,
    chat_id INTEGER
)
''')
conn.commit()

async def check_message(message: types.Message):
    if not CHAT_IDS or message.chat.id not in map(int, CHAT_IDS):  
        return 

    user_id = message.from_user.id
    username = message.from_user.username
    current_time = datetime.now()


    cursor.execute('SELECT timestamp FROM messages WHERE user_id = ? AND chat_id = ?', (user_id, message.chat.id))
    last_message = cursor.fetchone()

    if last_message:
        last_message_time = datetime.strptime(last_message[0], '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - last_message_time

        if time_diff < timedelta(hours=1):
            if not username:
                await bot.send_message(message.chat.id, f"Пользователь [{user_id}]\nВы можете отправить следующее сообщение только через час!")
            else:
                await bot.send_message(message.chat.id, f"@{username} [{user_id}]\nВы можете отправить следующее сообщение только через час!")

            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            logger.info(f"Сообщение {message.message_id} удалено в чате {message.chat.id}.")
        else:
            cursor.execute('UPDATE messages SET timestamp = ? WHERE user_id = ? AND chat_id = ?', 
                           (current_time.strftime('%Y-%m-%d %H:%M:%S'), user_id, message.chat.id))
            conn.commit()
    else:
        cursor.execute('INSERT INTO messages (user_id, timestamp, chat_id) VALUES (?, ?, ?)', 
                       (user_id, current_time.strftime('%Y-%m-%d %H:%M:%S'), message.chat.id))
        conn.commit()

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    await check_message(message)

if __name__ == "__main__":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
