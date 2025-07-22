import json
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# 🔐 Bot tokeni va admin ID
API_TOKEN = '8181160347:AAGTFV-iVUcFS-NXkxxJ6VEZgFN7dzN-sPc'
ADMIN_ID = 5091466097

# 🔧 Logger sozlamalari
logging.basicConfig(level=logging.INFO)

# 🔄 Bot sozlamalari
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 📁 Foydalanuvchilar JSON fayli
USERS_FILE = "users.json"

# 🖼 Rasm ID va matn, tugma
PHOTO_URL = "https://img.freepik.com/free-vector/vip-background-design_1115-629.jpg?semt=ais_hybrid&w=740"

WELCOME_TEXT = """
𝗔𝘀𝘀𝗮𝗹𝗼𝗺𝘂 𝗮𝗹𝗮𝘆𝗸𝘂𝗺😊

𝗦𝗶𝘇 𝗩𝗶𝗽 𝗸𝗮𝗻𝗮𝗹 𝘃𝗮 𝗦𝗵𝗼𝗸𝗵 𝗮𝗸𝗲𝗻𝗶𝗻𝗴 𝟯𝟬𝟬𝟬$ 𝗹𝗶𝗸 𝗸𝘂𝗿𝘀𝗶𝗻𝗶 𝘆𝘂𝘁𝗶𝗯 𝗼𝗹𝗱𝗶𝗻𝗴𝗶𝘇😎

𝗨𝗹𝗮𝗿𝗻𝗶 𝗾𝗼𝗹𝗴𝗮 𝗸𝗶𝗿𝗶𝘁𝗶𝘀𝗵 𝘂𝗰𝗵𝘂𝗻 𝗽𝗮𝘀𝗱𝗮𝗴𝗶 𝗧𝘂𝗴𝗺𝗮𝗹𝗮𝗿𝗱𝗮𝗻 𝗳𝗼𝘆𝗱𝗮𝗹𝗮𝗻𝗶𝗻𝗴👇👇
"""

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📥 VIP Kanalga kirish", url="https://t.me/+dBQ_nO65OS82NDIy")],
    [InlineKeyboardButton(text="🎁 Kursni olish", url="https://t.me/+CHczj85tbcA4YTVi")]
])

# ✅ Foydalanuvchini faylga saqlovchi funksiya
def save_user(user_id: int):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

# 👋 /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    save_user(message.from_user.id)
    await message.answer("👋 Assalomu alaykum! Siz botga muvaffaqiyatli start berdingiz.")

# 🔔 Guruhga kirish so‘rovi kelganda faqat xabar yuboriladi, approve yo‘q
@dp.chat_join_request()
async def join_request_handler(request: ChatJoinRequest):
    try:
        save_user(request.from_user.id)

        # 🔔 Foydalanuvchiga rasm va tugmali xabar yuborish
        await bot.send_photo(
            chat_id=request.from_user.id,
            photo=PHOTO_URL,
            caption=WELCOME_TEXT,
            reply_markup=keyboard
        )
    except Exception as e:
        logging.warning(f"Xatolik: foydalanuvchiga xabar yuborilmadi: {request.from_user.id}")
        logging.exception(e)


# 📤 Admin uchun /sendall komanda
@dp.message(Command("sendall"))
async def send_all_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("✏️ Xabar matnini yozing: /sendall Matn")
        return

    msg = text[1]

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    success, failed = 0, 0
    for user_id in users:
        try:
            await bot.send_message(user_id, msg)
            success += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1

    await message.answer(f"📤 Yuborildi: {success} ta\n❌ Yuborilmadi: {failed} ta")

# ▶️ Botni ishga tushiramiz
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
