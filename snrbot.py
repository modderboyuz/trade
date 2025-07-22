import json
import logging
import asyncio
import os
import aiofiles
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, Update
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiohttp.web_app import Application

# 🔐 Bot tokeni va admin ID (environment variables dan olinadi)
API_TOKEN = os.getenv('BOT_TOKEN', '8181160347:AAGTFV-iVUcFS-NXkxxJ6VEZgFN7dzN-sPc')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5091466097'))

# 🌐 Webhook sozlamalari
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_SECRET = "my-secret"
BASE_WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')

# 🔧 Logger sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 🔄 Bot sozlamalari
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 📁 Foydalanuvchilar JSON fayli
USERS_FILE = "users.json"

# 🖼 Rasm URL va matn, tugma
PHOTO_URL = "https://img.freepik.com/free-vector/vip-background-design_1115-629.jpg"

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
async def save_user(user_id: int):
    try:
        # Fayl mavjudligini tekshirish
        if os.path.exists(USERS_FILE):
            async with aiofiles.open(USERS_FILE, "r", encoding="utf-8") as f:
                content = (await f.read()).strip()
                if content:
                    users = json.loads(content)
                else:
                    users = []
        else:
            users = []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Faylni o'qishda xatolik: {e}")
        users = []

    if user_id not in users:
        users.append(user_id)
        try:
            async with aiofiles.open(USERS_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(users, indent=4, ensure_ascii=False))
            logger.info(f"Yangi foydalanuvchi saqlandi: {user_id}")
        except Exception as e:
            logger.error(f"Foydalanuvchini saqlashda xatolik: {e}")

# 📊 Foydalanuvchilar sonini olish
async def get_users_count():
    try:
        if os.path.exists(USERS_FILE):
            async with aiofiles.open(USERS_FILE, "r", encoding="utf-8") as f:
                content = (await f.read()).strip()
                if content:
                    users = json.loads(content)
                    return len(users)
        return 0
    except Exception as e:
        logger.error(f"Foydalanuvchilar sonini olishda xatolik: {e}")
        return 0

# 👋 /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    try:
        await save_user(message.from_user.id)
        user_name = message.from_user.first_name or "Foydalanuvchi"
        await message.answer(f"👋 Assalomu alaykum, {user_name}! Siz botga muvaffaqiyatli start berdingiz.")
        logger.info(f"Start komandasi: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Start komandasi xatoligi: {e}")

# 📊 /stats komandasi (faqat admin uchun)
@dp.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        users_count = await get_users_count()
        await message.answer(f"📊 Bot statistikasi:\n👥 Jami foydalanuvchilar: {users_count}")
    except Exception as e:
        logger.error(f"Stats komandasi xatoligi: {e}")
        await message.answer("❌ Statistikani olishda xatolik yuz berdi.")

# 🔔 Guruhga kirish so'rovi kelganda
@dp.chat_join_request()
async def join_request_handler(request: ChatJoinRequest):
    try:
        await save_user(request.from_user.id)
        
        # 🔔 Foydalanuvchiga rasm va tugmali xabar yuborish
        await bot.send_photo(
            chat_id=request.from_user.id,
            photo=PHOTO_URL,
            caption=WELCOME_TEXT,
            reply_markup=keyboard
        )
        logger.info(f"Join request xabari yuborildi: {request.from_user.id}")
    except Exception as e:
        logger.warning(f"Join request xabarini yuborishda xatolik: {request.from_user.id} - {e}")

# 📤 Admin uchun /sendall komanda
@dp.message(Command("sendall"))
async def send_all_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Sizda bu komandani ishlatish huquqi yo'q!")
        return

    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("✏️ Xabar matnini yozing:\n<code>/sendall Sizning xabaringiz</code>")
        return

    msg = text[1]

    try:
        if os.path.exists(USERS_FILE):
            async with aiofiles.open(USERS_FILE, "r", encoding="utf-8") as f:
                content = (await f.read()).strip()
                if content:
                    users = json.loads(content)
                else:
                    users = []
        else:
            users = []
    except Exception as e:
        logger.error(f"Foydalanuvchilar ro'yxatini o'qishda xatolik: {e}")
        await message.answer("❌ Foydalanuvchilar ro'yxatini o'qishda xatolik!")
        return

    if not users:
        await message.answer("📭 Hech qanday foydalanuvchi topilmadi!")
        return

    # Yuborish jarayoni haqida xabar
    status_msg = await message.answer(f"📤 {len(users)} ta foydalanuvchiga xabar yuborilmoqda...")

    success, failed = 0, 0
    for i, user_id in enumerate(users):
        try:
            await bot.send_message(user_id, msg)
            success += 1
            await asyncio.sleep(0.05)  # Rate limiting uchun
            
            # Har 50 ta xabardan keyin progress yangilanadi
            if (i + 1) % 50 == 0:
                await status_msg.edit_text(
                    f"📤 Jarayon: {i + 1}/{len(users)}\n"
                    f"✅ Yuborildi: {success}\n"
                    f"❌ Yuborilmadi: {failed}"
                )
        except Exception as e:
            failed += 1
            logger.warning(f"Xabar yuborishda xatolik {user_id}: {e}")

    # Yakuniy natija
    await status_msg.edit_text(
        f"📤 Xabar yuborish yakunlandi!\n"
        f"✅ Muvaffaqiyatli: {success} ta\n"
        f"❌ Muvaffaqiyatsiz: {failed} ta\n"
        f"📊 Jami: {len(users)} ta"
    )

# 🛠 Xatoliklarni tutuvchi handler
@dp.message()
async def echo_handler(message: Message):
    try:
        # Faqat admin uchun echo
        if message.from_user.id == ADMIN_ID:
            await message.answer(f"Echo: {message.text}")
    except Exception as e:
        logger.error(f"Echo handler xatoligi: {e}")

# 🌐 Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is running! 🤖", status=200)

# 🌐 Root endpoint
async def root_handler(request):
    return web.Response(
        text="""
        🤖 Telegram VIP Bot is running!
        
        Bot features:
        ✅ User registration
        📊 Admin statistics  
        📤 Broadcast messages
        🔔 Join request handling
        
        Status: Active ✅
        """, 
        status=200,
        content_type='text/plain'
    )

# 🚀 Webhook o'rnatish
async def on_startup():
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    try:
        # Avvalgi webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Yangi webhook o'rnatish
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        
        # Bot ma'lumotlarini olish
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ishga tushdi: @{bot_info.username}")
        logger.info(f"🌐 Webhook o'rnatildi: {webhook_url}")
        
    except Exception as e:
        logger.error(f"❌ Webhook o'rnatishda xatolik: {e}")

# 🛑 Webhook o'chirish
async def on_shutdown():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi va webhook o'chirildi")
    except Exception as e:
        logger.error(f"❌ Shutdown xatoligi: {e}")

# ▶️ Web server yaratish va ishga tushirish
def create_app() -> Application:
    app = web.Application()
    
    # Webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # HTTP endpoints
    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_check)
    
    # Startup va shutdown eventlari
    app.on_startup.append(lambda app: asyncio.create_task(on_startup()))
    app.on_shutdown.append(lambda app: asyncio.create_task(on_shutdown()))
    
    return app

# 🚀 Main funksiya
def main():
    try:
        app = create_app()
        
        # Port ni environment variable dan olish (Render avtomatik beradi)
        port = int(os.getenv('PORT', 8080))
        
        logger.info(f"🚀 Server {port} portda ishga tushmoqda...")
        
        # Web server ishga tushirish
        web.run_app(
            app,
            host='0.0.0.0',
            port=port,
            access_log=logger
        )
        
    except Exception as e:
        logger.error(f"❌ Server ishga tushirishda xatolik: {e}")

if __name__ == "__main__":
    main()