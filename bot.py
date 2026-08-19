import asyncio
import logging
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
GROUP_IDS_FILE = "group_ids.txt"

# ---------- LARGE POOL OF RELATED TOPICS (30+ messages) ----------
TOPIC_POOL = [
    "📊 Did you know? Passive income streams are growing 20% year over year.",
    "💡 The best time to start earning in crypto was yesterday – the second best is today.",
    "👥 Team leaders earn more than solo players. Build your downline and multiply rewards.",
    "📈 Market volatility is your friend – our VIP plan helps you hedge against dips.",
    "🏆 Top earners in our program make 5x more by referring just 10 active users.",
    "⏳ Every minute you wait is a missed opportunity. Join the winning team now.",
    "🔐 Security first – our platform uses bank-grade encryption for all transactions.",
    "🚀 Crypto adoption is skyrocketing – get ahead of the curve with our VIP tier.",
    "🧠 Education is key. We provide daily tips to help you maximise your earnings.",
    "💎 VIP members enjoy early access to new features and higher staking rewards.",
    "📱 Mobile-friendly dashboard – manage your earnings from anywhere.",
    "🔄 Compounding is the 8th wonder. Our 3.5% daily return compounds fast.",
    "🤝 Community matters – join our official channel and connect with top earners.",
    "📅 Daily payouts? Yes! We process withdrawals within 24 hours.",
    "🌟 Real testimonials: 'I doubled my investment in 3 months with this program.'",
    "📊 Diversify your portfolio – our plan is a stable high-yield addition.",
    "⏰ The early bird gets the worm. Register now before the next bonus round ends.",
    "🔥 Referral bonuses are unlimited – earn even when your team grows.",
    "🏦 No hidden fees – what you see is what you earn.",
    "📈 Our algorithm adjusts to market trends to keep your yield consistent.",
    "💬 24/7 support team – we're here to answer all your questions.",
    "🎯 Set your daily earning goal and watch it become reality.",
    "🧩 Team commission structure is transparent – up to 0.6% for leaders.",
    "🌍 Global community – users from 50+ countries are already earning.",
    "🛡️ Risk management tools included – protect your capital while earning.",
    "📆 Monthly leaderboard competitions – win extra prizes for top performers.",
    "💼 Treat this like a side business – it has real income potential.",
    "📲 Instant notifications for every transaction – stay in control.",
    "🔗 Share your referral link and start earning within minutes.",
    "🏅 Become a team leader and unlock exclusive training sessions.",
    "💸 Withdraw your earnings anytime – no lock‑in periods.",
    "📈 VIP interest rate just increased to 3.5% – now is the perfect time."
]

# Your fixed call‑to‑action (sent at the very end)
FINAL_CALL = (
    "✅ VIP has increased to 3.5% + 3📌\n\n"
    "🪙 REGISTER HERE ⏩⏩ https://app-web.mobiuspe-app.com/regist?code=earnmoney426\n\n"
    "✅ We offer team leader salaries and up to 0.6% team commission. Please contact us to apply for a team leader position. 🛒\n\n"
    "Official channel link ⭐️ https://t.me/mobiuspayofficial1\n"
    "Contact support ⭐️ @puya1521"
)

scheduler = AsyncIOScheduler(timezone="UTC")  # change to your timezone if needed

# ---------- Group ID persistence ----------
def load_group_ids():
    try:
        with open(GROUP_IDS_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip().isdigit()]
    except FileNotFoundError:
        return []

def save_group_id(chat_id):
    ids = load_group_ids()
    if chat_id not in ids:
        ids.append(chat_id)
        with open(GROUP_IDS_FILE, "w") as f:
            for cid in ids:
                f.write(f"{cid}\n")

async def send_to_all_groups(context, text):
    for cid in load_group_ids():
        try:
            await context.bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Failed to send to {cid}: {e}")

# ---------- The daily 1‑hour session ----------
async def daily_session(context):
    # 1. Seed the random shuffle with today's date so the order changes daily
    today_seed = datetime.now().date().toordinal()
    random.seed(today_seed)
    shuffled = random.sample(TOPIC_POOL, len(TOPIC_POOL))  # shuffle all

    # 2. Pick how many messages to send in 1 hour (every 4 minutes => ~15)
    #    We'll send one every 4 minutes (240 seconds). Adjust as you like.
    interval_seconds = 240   # 4 minutes
    max_messages = 60 * 60 // interval_seconds  # 15

    # 3. Send the selected messages
    for i in range(min(max_messages, len(shuffled))):
        msg = shuffled[i]
        await send_to_all_groups(context, msg)
        if i < max_messages - 1:
            await asyncio.sleep(interval_seconds)

    # 4. After the hour, send the FINAL CALL (your specific details)
    await asyncio.sleep(5)  # short pause
    await send_to_all_groups(context, FINAL_CALL)

# Scheduler wrapper
def start_daily_session(context):
    asyncio.create_task(daily_session(context))

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is active! I'll share daily insights and special offers.")

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        save_group_id(chat.id)
        await update.message.reply_text("✅ This group is now registered for daily broadcasts.")
    else:
        await update.message.reply_text("Please add me to a group first.")

async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        save_group_id(chat.id)
        await context.bot.send_message(chat_id=chat.id, text="🎉 Thanks for adding me! I'll post daily insights and offers at the scheduled time.")

# ---------- Main ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addgroup", add_group))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_group))

    # Schedule daily at 10:00 UTC (adjust hour/minute)
    scheduler.add_job(
        start_daily_session,
        "cron",
        hour=10,
        minute=0,
        args=[app]
    )
    scheduler.start()

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
