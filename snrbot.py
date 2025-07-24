import json
import logging
import asyncio
import os
import aiofiles
import asyncpg
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, Update, User
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiohttp.web_app import Application
from dotenv import load_dotenv

# Environment variables yuklash
load_dotenv()

# 🔐 Bot tokeni va admin ID (environment variables dan olinadi)
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID_STR = os.getenv('ADMIN_ID')

if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

if not ADMIN_ID_STR:
    raise ValueError("ADMIN_ID environment variable is required!")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    raise ValueError("ADMIN_ID must be a valid integer!")

# 🗄️ Database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required!")

# 🌐 Webhook sozlamalari
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_SECRET = "my-secret"
BASE_WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    raise ValueError("RENDER_EXTERNAL_URL environment variable is required!")

# 🔧 Logger sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 🔄 Bot sozlamalari
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 🗄️ Database connection pool
db_pool = None

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

# 🗄️ Database connection yaratish
async def create_db_pool():
    global db_pool
    try:
        logger.info(f"🔗 Database ga ulanmoqda: {DATABASE_URL[:50]}...")
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
            server_settings={
                'application_name': 'telegram_bot'
            }
        )
        logger.info("✅ Database connection pool yaratildi")
        
        # Database jadvalini tekshirish va yaratish
        await init_database()
        
    except Exception as e:
        logger.error(f"❌ Database connection xatoligi: {e}")
        # Database xatoligi bo'lsa ham bot ishlashini davom ettirish
        logger.warning("⚠️ Bot database siz ishlaydi")

# 🗄️ Database jadvalini yaratish
async def init_database():
    try:
        async with db_pool.acquire() as conn:
            # Users jadvalini yaratish
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    username TEXT,
                    language_code TEXT,
                    is_bot BOOLEAN DEFAULT FALSE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    last_activity TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Indexlar yaratish
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username) WHERE username IS NOT NULL
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_created_at 
                ON users(created_at)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_last_activity 
                ON users(last_activity)
            """)
            
            # Trigger function yaratish
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """)
            
            # Trigger yaratish
            await conn.execute("""
                DROP TRIGGER IF EXISTS update_users_updated_at ON users
            """)
            
            await conn.execute("""
                CREATE TRIGGER update_users_updated_at
                    BEFORE UPDATE ON users
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """)
            
        logger.info("✅ Database jadval va indexlar yaratildi")
        
    except Exception as e:
        logger.error(f"❌ Database init xatoligi: {e}")
        raise

# ✅ Foydalanuvchini database ga saqlovchi funksiya
async def save_user(user: User):
    if not db_pool:
        logger.warning("Database pool mavjud emas, foydalanuvchi saqlanmadi")
        return
        
    try:
        async with db_pool.acquire() as conn:
            # Foydalanuvchi mavjudligini tekshirish
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE id = $1", user.id
            )
            
            if existing_user:
                # Mavjud foydalanuvchini yangilash
                await conn.execute("""
                    UPDATE users SET 
                        first_name = $2,
                        last_name = $3,
                        username = $4,
                        language_code = $5,
                        is_bot = $6,
                        is_premium = $7,
                        last_activity = NOW()
                    WHERE id = $1
                """, 
                user.id,
                user.first_name,
                user.last_name,
                user.username,
                user.language_code,
                user.is_bot or False,
                user.is_premium or False
                )
                logger.info(f"Foydalanuvchi yangilandi: {user.id}")
            else:
                # Yangi foydalanuvchini qo'shish
                await conn.execute("""
                    INSERT INTO users (
                        id, first_name, last_name, username, 
                        language_code, is_bot, is_premium
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user.id,
                user.first_name,
                user.last_name,
                user.username,
                user.language_code,
                user.is_bot or False,
                user.is_premium or False
                )
                logger.info(f"Yangi foydalanuvchi saqlandi: {user.id}")
                
    except Exception as e:
        logger.error(f"Foydalanuvchini saqlashda xatolik: {e}")

# 📊 Foydalanuvchilar sonini olish
async def get_users_count():
    if not db_pool:
        return 0
        
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM users")
            return result or 0
    except Exception as e:
        logger.error(f"Foydalanuvchilar sonini olishda xatolik: {e}")
        return 0

# 📊 Batafsil statistika olish
async def get_detailed_stats():
    if not db_pool:
        return {
            'total': 0, 'today': 0, 'week': 0, 
            'month': 0, 'premium': 0, 'active': 0
        }
        
    try:
        async with db_pool.acquire() as conn:
            # Umumiy statistika
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            
            # Bugungi yangi foydalanuvchilar
            today_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            # Haftalik yangi foydalanuvchilar
            week_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            # Oylik yangi foydalanuvchilar
            month_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            
            # Premium foydalanuvchilar
            premium_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users WHERE is_premium = TRUE
            """)
            
            # Faol foydalanuvchilar (oxirgi 24 soatda)
            active_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE last_activity >= NOW() - INTERVAL '24 hours'
            """)
            
            return {
                'total': total_users or 0,
                'today': today_users or 0,
                'week': week_users or 0,
                'month': month_users or 0,
                'premium': premium_users or 0,
                'active': active_users or 0
            }
            
    except Exception as e:
        logger.error(f"Batafsil statistika olishda xatolik: {e}")
        return {
            'total': 0, 'today': 0, 'week': 0, 
            'month': 0, 'premium': 0, 'active': 0
        }

# 📤 Barcha foydalanuvchilar ID larini olish
async def get_all_user_ids():
    if not db_pool:
        return []
        
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM users ORDER BY created_at DESC")
            return [row['id'] for row in rows]
    except Exception as e:
        logger.error(f"Foydalanuvchilar ID larini olishda xatolik: {e}")
        return []

# 👋 /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    try:
        await save_user(message.from_user)
        
        # Rasm va tugmali xabar yuborish
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=PHOTO_URL,
            caption=WELCOME_TEXT,
            reply_markup=keyboard
        )
        logger.info(f"Start komandasi: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Start komandasi xatoligi: {e}")
        # Agar rasm yuborishda xatolik bo'lsa, oddiy matn yuborish
        try:
            user_name = message.from_user.first_name or "Foydalanuvchi"
            await message.answer(f"👋 Assalomu alaykum, {user_name}!\n\n{WELCOME_TEXT}")
        except Exception as e2:
            logger.error(f"Oddiy xabar yuborishda ham xatolik: {e2}")

# 📊 /stats komandasi (faqat admin uchun)
@dp.message(Command("stats"))
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        stats = await get_detailed_stats()
        
        stats_text = f"""
📊 <b>Bot Statistikasi</b>

👥 <b>Jami foydalanuvchilar:</b> {stats['total']:,}
📅 <b>Bugungi yangi:</b> {stats['today']:,}
📈 <b>Haftalik yangi:</b> {stats['week']:,}
📊 <b>Oylik yangi:</b> {stats['month']:,}
⭐ <b>Premium foydalanuvchilar:</b> {stats['premium']:,}
🟢 <b>Faol (24 soat):</b> {stats['active']:,}

🕐 <b>Yangilangan:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error(f"Stats komandasi xatoligi: {e}")
        await message.answer("❌ Statistikani olishda xatolik yuz berdi.")

# 🔔 Guruhga kirish so'rovi kelganda
@dp.chat_join_request()
async def join_request_handler(request: ChatJoinRequest):
    try:
        await save_user(request.from_user)
        
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
        users = await get_all_user_ids()
    except Exception as e:
        logger.error(f"Foydalanuvchilar ro'yxatini olishda xatolik: {e}")
        await message.answer("❌ Foydalanuvchilar ro'yxatini olishda xatolik!")
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
        # Har qanday xabar kelganda foydalanuvchini saqlash
        await save_user(message.from_user)
        
        # Faqat admin uchun echo
        if message.from_user.id == ADMIN_ID:
            await message.answer(f"Echo: {message.text}")
    except Exception as e:
        logger.error(f"Echo handler xatoligi: {e}")

# 🌐 Health check endpoint
async def health_check(request):
    db_status = "❌ Disconnected"
    db_error = None
    
    try:
        if db_pool:
            # Database connection tekshirish
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "✅ Connected"
        else:
            db_status = "❌ Pool not initialized"
    except Exception as e:
        db_status = "❌ Error"
        db_error = str(e)
    
    response_text = f"Bot is running! 🤖\nDatabase: {db_status}"
    if db_error:
        response_text += f"\nError: {db_error}"
    
    return web.Response(
        text=response_text, 
        status=200
    )

# 🌐 Root endpoint
async def root_handler(request):
    try:
        stats = await get_detailed_stats()
        
        return web.Response(
            text=f"""
🤖 Telegram VIP Bot is running!

Bot features:
✅ User registration with Supabase
📊 Advanced statistics  
📤 Broadcast messages
🔔 Join request handling

📊 Current Stats:
👥 Total users: {stats['total']:,}
📅 Today: {stats['today']:,}
📈 This week: {stats['week']:,}
📊 This month: {stats['month']:,}
⭐ Premium: {stats['premium']:,}
🟢 Active (24h): {stats['active']:,}

Status: Active ✅
Database: Connected ✅
            """, 
            status=200,
            content_type='text/plain'
        )
    except Exception as e:
        return web.Response(
            text=f"""
🤖 Telegram VIP Bot is running!

Status: Active ✅
Database: Error ❌
Error: {str(e)}
            """, 
            status=200,
            content_type='text/plain'
        )

# 🚀 Webhook o'rnatish
async def on_startup():
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    try:
        logger.info("🚀 Bot ishga tushmoqda...")
        
        # Database connection yaratish
        await create_db_pool()
        
        # Bot ma'lumotlarini olish
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot ma'lumotlari olindi: @{bot_info.username}")
        
        # Avvalgi webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🗑️ Avvalgi webhook o'chirildi")
        
        # Yangi webhook o'rnatish
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        logger.info(f"🌐 Webhook o'rnatildi: {webhook_url}")
        
        # Webhook holatini tekshirish
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📊 Webhook holati: {webhook_info.url}")
        
        logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
        
    except Exception as e:
        logger.error(f"❌ Startup xatoligi: {e}")
        raise

# 🛑 Webhook o'chirish
async def on_shutdown():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.session.close()
        
        # Database connection yopish
        if db_pool:
            await db_pool.close()
            
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