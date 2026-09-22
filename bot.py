import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# 🤖 ตั้งค่า Token
# =========================
TOKEN = os.environ.get("TOKEN")

# =========================
# 🌐 Flask keep-alive server
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# =========================
# 💰 ดึงราคาทอง
# =========================
def get_gold_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        data = r.json()
        price = data.get("price")
        if price:
            return f"🥇 ราคาทองคำโลก\n💰 ${price:,.2f} USD/oz"
        return "❌ ไม่พบข้อมูลราคาทอง"
    except Exception as e:
        return f"❌ ดึงราคาไม่สำเร็จ: {e}"

# =========================
# 📩 คำสั่งของบอท
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 สวัสดี! ฉันคือบอทราคาทอง\n"
        "พิมพ์ /price เพื่อดูราคาทองคำ"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_gold_price())

# =========================
# 🚀 เริ่มการทำงาน
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("TOKEN not found!")

    Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))

    print("✅ Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
