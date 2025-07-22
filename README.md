# Telegram VIP Bot (Web Service)

Bu bot VIP kanal va kurslar uchun mo'ljallangan Telegram bot. Webhook usuli bilan Web Service sifatida ishlaydi.

## 🌟 Xususiyatlari

- ✅ Foydalanuvchilarni avtomatik ro'yxatga olish
- 📊 Admin uchun statistika
- 📤 Barcha foydalanuvchilarga xabar yuborish
- 🔔 Guruhga kirish so'rovlarini qayta ishlash
- 🖼 Rasm va tugmalar bilan xabar yuborish
- 🌐 Webhook orqali ishlash (Web Service)
- 🏥 Health check endpoint

## 🚀 Render.com ga deploy qilish

### 1. Repository tayyorlash
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/telegram-bot.git
git push -u origin main
```

### 2. Render.com sozlamalari

**Service Type:** `Web Service` ✅

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python snrbot.py
```

**Environment Variables:**
- `BOT_TOKEN` = sizning bot tokeningiz
- `ADMIN_ID` = sizning Telegram ID raqamingiz
- `RENDER_EXTERNAL_URL` = https://your-app-name.onrender.com

### 3. Webhook URL
Bot avtomatik ravishda webhook o'rnatadi:
- Webhook URL: `https://your-app-name.onrender.com/webhook/BOT_TOKEN`
- Health check: `https://your-app-name.onrender.com/health`

## 📋 Komandalar

- `/start` - Botni ishga tushirish
- `/stats` - Statistika (faqat admin)
- `/sendall <xabar>` - Barcha foydalanuvchilarga xabar (faqat admin)

## 🔧 Texnik ma'lumotlar

- **Framework:** aiogram 3.13.1
- **Web Server:** aiohttp
- **Method:** Webhook
- **Port:** 8080 (yoki Render tomonidan berilgan)
- **Health Check:** `/health` endpoint

## 🌐 Endpoints

- `GET /` - Bot holati haqida ma'lumot
- `GET /health` - Health check
- `POST /webhook/{BOT_TOKEN}` - Telegram webhook

## 📊 Monitoring

Bot ishlab turganini tekshirish:
```bash
curl https://your-app-name.onrender.com/health
```

## ⚠️ Muhim eslatmalar

1. `RENDER_EXTERNAL_URL` ni to'g'ri o'rnating
2. Bot tokeni va admin ID ni environment variables ga qo'ying
3. Webhook avtomatik o'rnatiladi
4. Bot 24/7 ishlaydi

## 🔒 Xavfsizlik

- Bot tokeni environment variable sifatida saqlanadi
- Webhook secret token ishlatiladi
- Faqat admin komandalarni ishlatishi mumkin

## 📝 Litsenziya

MIT License