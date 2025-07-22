# Telegram VIP Bot

Bu bot VIP kanal va kurslar uchun mo'ljallangan Telegram bot.

## Xususiyatlari

- ✅ Foydalanuvchilarni avtomatik ro'yxatga olish
- 📊 Admin uchun statistika
- 📤 Barcha foydalanuvchilarga xabar yuborish
- 🔔 Guruhga kirish so'rovlarini qayta ishlash
- 🖼 Rasm va tugmalar bilan xabar yuborish

## O'rnatish

1. Repository ni clone qiling
2. Virtual environment yarating:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # yoki
   venv\Scripts\activate  # Windows
   ```
3. Kerakli paketlarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env` faylini yarating va bot tokenini qo'shing:
   ```
   BOT_TOKEN=your_bot_token_here
   ADMIN_ID=your_admin_id_here
   ```
5. Botni ishga tushiring:
   ```bash
   python snrbot.py
   ```

## Render.com ga deploy qilish

1. GitHub repository yarating va kodlarni yuklang
2. Render.com da yangi Web Service yarating
3. GitHub repository ni ulang
4. Environment Variables qo'shing:
   - `BOT_TOKEN`: Sizning bot tokeningiz
   - `ADMIN_ID`: Admin ID raqami
5. Deploy qiling

## Komandalar

- `/start` - Botni ishga tushirish
- `/stats` - Statistika (faqat admin)
- `/sendall <xabar>` - Barcha foydalanuvchilarga xabar (faqat admin)

## Litsenziya

MIT License