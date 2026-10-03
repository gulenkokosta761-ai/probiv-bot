# language: Python 3.11, file: probiv.py, runtime: aiogram 3.x
import asyncio, sqlite3, logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, CallbackQuery, LabeledPrice,
                           PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.client.default import DefaultBotProperties

TOKEN = "OXVEDOSE11bot"
OWNER_ID = 8624065969          # твой id из @userinfobot
PRICE = 5                     # звёзд за запрос
FREE = 3                      # бесплатных на старте

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
db = sqlite3.connect("users.db")
db.execute("CREATE TABLE IF NOT EXISTS u(id INTEGER PRIMARY KEY, free INTEGER DEFAULT 3, paid INTEGER DEFAULT 0)")
db.commit()

def get(uid):
    db.execute("INSERT OR IGNORE INTO u(id) VALUES(?)", (uid,))
    db.commit()
    return db.execute("SELECT free,paid FROM u WHERE id=?", (uid,)).fetchone()

def spend(uid, kind):
    db.execute(f"UPDATE u SET {kind}={kind}-1 WHERE id=?", (uid,)); db.commit()

@dp.message(F.text == "/start")
async def start(m: Message):
    get(m.from_user.id)
    await m.answer(
        "🔎 <b>Пробив-бот</b>\n\n"
        f"Тебе доступно <b>{FREE} бесплатных запроса</b>.\n"
        f"Дальше — <b>{PRICE}⭐</b> за запрос.\n\n"
        "Просто отправь данные для пробива (номер, ник, ФИО, @username):"
    )

@dp.message(F.text)
async def query(m: Message):
    uid = m.from_user.id
    free, paid = get(uid)
    if free <= 0 and paid <= 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"Оплатить {PRICE}⭐", callback_data="pay")
        ]])
        await m.answer(f"❌ Бесплатные кончились.\nОдин пробив — {PRICE}⭐.", reply_markup=kb)
        return
    if free > 0:
        spend(uid, "free")
        left = free - 1
        note = f"Осталось бесплатных: {left}"
    else:
        spend(uid, "paid")
        note = f"Осталось оплаченных: {paid-1}"

    await m.answer(f"⏳ Запрос принят: <code>{m.text[:80]}</code>\n{note}\n\nРезультат придёт в течение 24ч.")
    try:
        await bot.send_message(OWNER_ID,
            f"🔔 Пробив от {m.from_user.id} (@{m.from_user.username})\n{m.text}")
    except: pass

@dp.callback_query(F.data == "pay")
async def pay(cb: CallbackQuery):
    await cb.message.answer_invoice(
        title="Пробив — 1 запрос",
        description="Один запрос на пробив данных",
        payload="probiv1", currency="XTR",
        prices=[LabeledPrice(label="Пробив", amount=PRICE)],
        provider_token=""
    )
    await cb.answer()

@dp.pre_checkout_query()
async def pco(q: PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: Message):
    db.execute("UPDATE u SET paid=paid+1 WHERE id=?", (m.from_user.id,)); db.commit()
    await m.answer(f"✅ +1 запрос за {PRICE}⭐. Отправь данные для пробива.")

async def main(): await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
