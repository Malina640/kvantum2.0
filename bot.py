
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime
import re

API_TOKEN = "7790662231:AAFzWl1jAqajyx29OW4JVa7-mkSlCrTjiEQ"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = sqlite3.connect("kvanto.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT, reminder_time TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS answers (user_id INTEGER, date TEXT, q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT)")
conn.commit()

class Form(StatesGroup):
    name = State()
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        await message.answer(f"Привет снова, {row[0]}! Напиши /practice чтобы начать.")
    else:
        await message.answer("Привет! Как тебя зовут?")
        await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text
    cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    await message.answer(f"Рад знакомству, {name}! Готов начать?")
    await message.answer("Вопрос 1: Что сегодня приблизило тебя к деньгам?")
    await Form.q1.set()

@dp.message_handler(state=Form.q1)
async def q1(message: types.Message, state: FSMContext):
    await state.update_data(q1=message.text)
    await message.answer("Вопрос 2: Где ты почувствовал движение вперёд?")
    await Form.q2.set()

@dp.message_handler(state=Form.q2)
async def q2(message: types.Message, state: FSMContext):
    await state.update_data(q2=message.text)
    await message.answer("Вопрос 3: Что уводило тебя в сторону?")
    await Form.q3.set()

@dp.message_handler(state=Form.q3)
async def q3(message: types.Message, state: FSMContext):
    await state.update_data(q3=message.text)
    await message.answer("Вопрос 4: Как ты можешь завтра быть ближе к деньгам?")
    await Form.q4.set()

@dp.message_handler(state=Form.q4)
async def q4(message: types.Message, state: FSMContext):
    await state.update_data(q4=message.text)
    await message.answer("И наконец — твоя микроаффирмация на завтра?")
    await Form.q5.set()

@dp.message_handler(state=Form.q5)
async def q5(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    q1, q2, q3, q4, q5 = data['q1'], data['q2'], data['q3'], data['q4'], message.text
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO answers VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, today, q1, q2, q3, q4, q5))
    conn.commit()
    await message.answer(
        f"🎯 Вот твой день:
"
        f"1. {q1}
2. {q2}
3. {q3}
4. {q4}
5. {q5}

"
        f"🥇 Успешный успех: {q1}
🥴 Жмых: {q3}

"
        f"💡 Совет на завтра: продолжай делать то, что приближает тебя к деньгам."
    )
    await state.finish()

@dp.message_handler(commands=['settime'])
async def set_time(message: types.Message):
    await message.answer("Во сколько тебе удобно получать вопросы? Напиши в формате ЧЧ:ММ")

@dp.message_handler(lambda msg: re.match(r'^\d{1,2}:\d{2}$', msg.text))
async def save_time(message: types.Message):
    try:
        datetime.strptime(message.text, "%H:%M")
        cursor.execute("UPDATE users SET reminder_time=? WHERE user_id=?", (message.text, message.from_user.id))
        conn.commit()
        await message.answer(f"Ок! Буду писать каждый день в {message.text}")
    except:
        await message.answer("Формат времени неправильный. Попробуй ещё раз: ЧЧ:ММ")

@dp.message_handler(commands=['совет'])
async def advise(message: types.Message):
    await message.answer("💡 Совет: выбери один шаг, который реально двигает тебя к цели — и сделай его первым.")

@dp.message_handler(commands=['practice'])
async def practice(message: types.Message):
    await start(message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
