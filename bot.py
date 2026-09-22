import requests
import threading
import time
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask

import os
TOKEN = os.environ.get("TOKEN")
TH_TZ = timezone(timedelta(hours=7))

# ---------- ดึงราคาทอง (ฟรี) ----------
def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return r.json()["price"]
    except:
        try:
            r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10)
            return r.json()["items"][0]["xauPrice"]
        except:
            return None

def get_usd_thb():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        return r.json()["rates"]["THB"]
    except:
        return 35.0

def to_baht(gold_usd_oz):
    usd_thb = get_usd_thb()
    grams = gold_usd_oz / 31.1035
    return grams * 15.244 * 0.965 * 1.03 * usd_thb

# ---------- สถานะตลาด ----------
def market_status():
    now = datetime.now(TH_TZ)
    day, hour = now.weekday(), now.hour
    if (day == 5 and hour >= 4) or day == 6:
        return "🔴 ตลาดปิด (สุดสัปดาห์) — เปิดจันทร์ ~05:00 น."
    if day == 0 and hour < 5:
        return "🔴 ตลาดปิด — เปิดจันทร์ 05:00 น. (เวลาไทย)"
    return "🟢 ตลาดเปิดอยู่ | ปิดเสาร์ 04:00 น."

# ---------- Commands ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bot ราคาทองคำ\n\n"
        "/price — ราคาตอนนี้\n"
        "/signal — สัญญาณซื้อ/ขาย\n"
        "/time — เวลาเปิด-ปิดตลาด"
    )

async def price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    g = get_gold()
    if not g:
        await update.message.reply_text("❌ ดึงราคาไม่ได้ ลองใหม่")
        return
    await update.message.reply_text(
        f"💰 ทองโลก: {g:,.2f} USD/ออนซ์\n"
        f"🇹🇭 ≈ {to_baht(g):,.0f} บาท/บาททอง (ประมาณ)\n\n"
        f"📅 {datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M')} น.\n"
        f"{market_status()}"
    )

async def signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    g = get_gold()
    if not g:
        await update.message.reply_text("❌ ดึงราคาไม่ได้")
        return
    if g > 2700:
        msg = "📈 โซนสูง — ระวังแรงขายทำกำไร ไม่แนะนำซื้อมือใหม่"
    elif g < 2400:
        msg = "📉 โซนต่ำ — โซนสะสม ซื้อแบ่งไม้"
    else:
        msg = "⚖️ กลางโซน — รอย่อซื้อ 1-2% / ขายเมื่อมีกำไร"
    await update.message.reply_text(f"📊 ราคา {g:,.2f} USD\n\n{msg}\n\n{market_status()}\n⚠️ ไม่ใช่คำแนะนำลงทุน")

async def time_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕐 ตลาดทองโลก (เวลาไทย)\n\n"
        "🟢 เปิด: จันทร์ 05:00 น.\n"
        "🔴 ปิด: เสาร์ 04:00 น.\n\n"
        f"ตอนนี้: {market_status()}"
    )

# ---------- Flask keep-alive (Render ต้องมี port เปิด) ----------
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return "Gold Bot is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# ---------- เริ่ม Bot ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("time", time_cmd))
    print("Bot running...")
    app.run_polling()
