import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import sqlite3
import aiofiles

# Токен вашего бота
API_TOKEN = '7488318384:AAGqDQF_kD5p8VwhrNycf8J3If5-ps4cCO4'

# Путь к файлу конфигурации
CHAT_ID_FILE = 'config.txt'

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание экземпляров бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Функция для загрузки CHAT_ID из файла
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

# Функция для записи CHAT_ID в файл
async def save_chat_id(chat_id):
    try:
        async with aiofiles.open(CHAT_ID_FILE, 'a') as f:
            await f.write(f"{chat_id}\n")
        logger.info(f"CHAT_ID {chat_id} успешно сохранен.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении CHAT_ID: {e}")

# Функция для записи списка chat_id в файл
async def save_chat_ids(chat_ids):
    try:
        async with aiofiles.open(CHAT_ID_FILE, 'w') as f:  # Используем асинхронный метод
            for chat_id in chat_ids:
                await f.write(f"{chat_id}\n")
        logger.info("CHAT_IDs успешно сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении CHAT_IDs: {e}")

# Функция для удаления chat_id из файла
async def delete_chat_id(chat_id):
    # Получаем список chat_id
    global CHAT_IDS
    chat_ids = load_chat_ids()

    # Убираем chat_id из списка
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        # Сохраняем измененный список в файл
        await save_chat_ids(chat_ids)

        # Удаляем chat_id из базы данных
        delete_chat_id_from_db(chat_id)

# Функция для удаления chat_id из базы данных
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

# Обработчик нажатий на инлайн кнопки для удаления каналов
@dp.callback_query_handler(lambda c: c.data == 'delete_chat_id')
async def delete_chat(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == ADMIN_ID:
        # Загружаем список каналов
        global CHAT_IDS
        chat_ids = load_chat_ids()
        
        if chat_ids:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for chat_id in chat_ids:
                try:
                    chat = await bot.get_chat(chat_id)  # Получаем данные о чате
                    chat_name = chat.username if chat.username else chat.title  # Получаем имя канала или группы
                    
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

# Обработчик нажатия на кнопку для удаления выбранного канала
@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def delete_chat(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == ADMIN_ID:
        chat_id = callback_query.data.split('_')[1]  # Извлекаем chat_id из callback_data
        
        # Удаляем chat_id из списка
        await delete_chat_id(chat_id)

        # Обновляем список каналов после удаления
        global CHAT_IDS
        CHAT_IDS = load_chat_ids()  # Заново загружаем актуализированный список каналов
        
        # Отправляем пользователю сообщение об успешном удалении
        await bot.send_message(callback_query.from_user.id, f"Канал с ID {chat_id} был успешно удален.")

        # Оповещаем об обновленном списке каналов
        await bot.answer_callback_query(callback_query.id)
    else:
        await bot.send_message(callback_query.from_user.id, "У вас нет прав для удаления канала.")

# Получаем список каналов из файла
CHAT_IDS = load_chat_ids()

# Если нет каналов, сообщаем об ошибке
if not CHAT_IDS:
    logger.error("Нет сохранённых CHAT_ID в файле!")

# Получаем ID админа (замените на свой ID)
ADMIN_ID = 511301057  # Укажите ваш ID

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопки для изменения или получения CHAT_ID
    set_chat_button = InlineKeyboardButton("Добавить новый канал по @username", callback_data='set_chat_id')
    delete_chat_button = InlineKeyboardButton("Удалить канал", callback_data='delete_chat_id')

    keyboard.add(set_chat_button, delete_chat_button)
    
    # Отправляем сообщение с инлайн-кнопками
    await message.answer(f"Привет, вы админ!", reply_markup=keyboard)

# Обработчик нажатий на инлайн кнопки
@dp.callback_query_handler(lambda c: c.data == 'set_chat_id')
async def set_chat_id(callback_query: types.CallbackQuery):
    # Обновляем текст текущего сообщения
    await bot.edit_message_text(
        text="Пожалуйста, отправьте @username группы.",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None  # Убираем клавиатуру
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(lambda message: message.text.startswith('@'))
async def set_chat_id_by_username(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            group_username = message.text.strip()

            # Получаем информацию о чате по username
            chat = await bot.get_chat(group_username)
            new_chat_id = chat.id

            await save_chat_id(new_chat_id)  # Сохраняем новый CHAT_ID в файл
            global CHAT_IDS
            CHAT_IDS = load_chat_ids()  # Обновляем список каналов

            # Инлайн-клавиатура с кнопкой возврата
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


# Обработчик возврата в главное меню
@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def back_to_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Кнопки для изменения или получения CHAT_ID
    set_chat_button = InlineKeyboardButton("Добавить новый канал по @username", callback_data='set_chat_id')
    delete_chat_button = InlineKeyboardButton("Удалить канал", callback_data='delete_chat_id')

    keyboard.add(set_chat_button, delete_chat_button)

    # Редактируем сообщение с кнопками
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Привет, вы админ!",
        reply_markup=keyboard
    )

# Подключение к базе данных SQLite
conn = sqlite3.connect('messages.db')  # Название файла базы данных
cursor = conn.cursor()

# Создание таблицы, если она не существует
cursor.execute(''' 
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    timestamp TEXT,
    chat_id INTEGER
)
''')
conn.commit()

# Функция для проверки сообщения и его удаления, если нарушен часовой интервал
async def check_message(message: types.Message):
    if not CHAT_IDS or message.chat.id not in map(int, CHAT_IDS):  # Проверка, что chat_id в списке
        return  # Игнорируем сообщения из других чатов, если они не в списке CHAT_IDS

    user_id = message.from_user.id
    username = message.from_user.username
    current_time = datetime.now()

    # Проверяем последнее сообщение
    cursor.execute('SELECT timestamp FROM messages WHERE user_id = ? AND chat_id = ?', (user_id, message.chat.id))
    last_message = cursor.fetchone()

    if last_message:
        last_message_time = datetime.strptime(last_message[0], '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - last_message_time

        if time_diff < timedelta(hours=1):
            # Если у пользователя нет @username
            if not username:
                await bot.send_message(message.chat.id, f"Пользователь [{user_id}]\nВы можете отправить следующее сообщение только через час!")
            else:
                # Формируем сообщение с упоминанием пользователя и его ID
                await bot.send_message(message.chat.id, f"@{username} [{user_id}]\nВы можете отправить следующее сообщение только через час!")

            # Удаляем сообщение, так как оно нарушает правило
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

# Обработчик для новых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    await check_message(message)

# Запуск бота с обработкой ошибок
if __name__ == "__main__":
    try:
        # Для Windows нужно явно указать использование SelectorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
