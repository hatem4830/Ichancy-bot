import sqlite3 import asyncio from aiogram import Bot, Dispatcher, types, executor from aiogram.types import ReplyKeyboardMarkup, KeyboardButton from aiogram.dispatcher import FSMContext from aiogram.dispatcher.filters.state import State, StatesGroup from aiogram.contrib.fsm_storage.memory import MemoryStorage

===== إعداد التوكن =====

TOKEN = "YOUR_BOT_TOKEN"  # استبدلها بالتوكن الحقيقي ADMIN_ID = 123456789       # ضع هنا رقم Telegram ID الخاص بالمشرف

===== إنشاء البوت والمخزن =====

storage = MemoryStorage() bot = Bot(token=TOKEN) dp = Dispatcher(bot, storage=storage)

===== إنشاء قاعدة البيانات =====

conn = sqlite3.connect('ecurrency.db') c = conn.cursor() c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, balance REAL DEFAULT 0)''') c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, amount REAL, status TEXT DEFAULT 'pending')''') conn.commit()

===== الكيبوردات =====

main_kb = ReplyKeyboardMarkup(resize_keyboard=True) main_kb.add(KeyboardButton('💰 إيداع'), KeyboardButton('💸 سحب')) main_kb.add(KeyboardButton('📊 الرصيد'))

admin_kb = ReplyKeyboardMarkup(resize_keyboard=True) admin_kb.add(KeyboardButton('📥 الطلبات المعلقة'))

===== حالات FSM =====

class Deposit(StatesGroup): amount = State()

class Withdraw(StatesGroup): amount = State()

===== تسجيل المستخدم =====

@dp.message_handler(commands=['start']) async def start(message: types.Message): user_id = message.from_user.id c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) if not c.fetchone(): c.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,)) conn.commit() await message.answer('مرحباً بك في نظام إيشنسي!\nيمكنك إدارة عمليات الإيداع والسحب بسهولة.', reply_markup=main_kb)

===== عرض الرصيد =====

@dp.message_handler(lambda message: message.text == '📊 الرصيد') async def balance(message: types.Message): c.execute('SELECT balance FROM users WHERE user_id = ?', (message.from_user.id,)) bal = c.fetchone()[0] await message.answer(f'رصيدك الحالي هو: {bal} 💵')

===== طلب إيداع =====

@dp.message_handler(lambda message: message.text == '💰 إيداع') async def deposit(message: types.Message): await message.answer('أدخل المبلغ الذي ترغب بإيداعه:') await Deposit.amount.set()

@dp.message_handler(state=Deposit.amount) async def process_deposit(message: types.Message, state: FSMContext): try: amount = float(message.text) c.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (message.from_user.id, 'deposit', amount)) conn.commit() await message.answer('تم إرسال طلب الإيداع. سيتم مراجعته من الإدارة قريباً.') await bot.send_message(ADMIN_ID, f'🔔 طلب إيداع جديد من المستخدم {message.from_user.id}\nالمبلغ: {amount}') except ValueError: await message.answer('الرجاء إدخال رقم صالح.') await state.finish()

===== طلب سحب =====

@dp.message_handler(lambda message: message.text == '💸 سحب') async def withdraw(message: types.Message): await message.answer('أدخل المبلغ الذي ترغب بسحبه:') await Withdraw.amount.set()

@dp.message_handler(state=Withdraw.amount) async def process_withdraw(message: types.Message, state: FSMContext): try: amount = float(message.text) c.execute('SELECT balance FROM users WHERE user_id = ?', (message.from_user.id,)) bal = c.fetchone()[0] if amount > bal: await message.answer('الرصيد غير كافٍ.') else: c.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (message.from_user.id, 'withdraw', amount)) conn.commit() await message.answer('تم إرسال طلب السحب. سيتم مراجعته من الإدارة قريباً.') await bot.send_message(ADMIN_ID, f'🔔 طلب سحب جديد من المستخدم {message.from_user.id}\nالمبلغ: {amount}') except ValueError: await message.answer('الرجاء إدخال رقم صالح.') await state.finish()

===== لوحة الإدارة =====

@dp.message_handler(commands=['admin']) async def admin_panel(message: types.Message): if message.from_user.id == ADMIN_ID: await message.answer('مرحباً أيها المدير 👑', reply_markup=admin_kb)

@dp.message_handler(lambda message: message.text == '📥 الطلبات المعلقة' and message.from_user.id == ADMIN_ID) async def pending_requests(message: types.Message): c.execute('SELECT id, user_id, type, amount FROM transactions WHERE status = "pending"') rows = c.fetchall() if not rows: await message.answer('لا توجد طلبات معلقة.') return for r in rows: await message.answer(f"ID:{r[0]} | المستخدم:{r[1]} | النوع:{r[2]} | المبلغ:{r[3]}")

===== تشغيل البوت =====

if name == 'main': executor.start_polling(dp, skip_updates=True)
