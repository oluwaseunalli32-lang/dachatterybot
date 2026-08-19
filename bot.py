import asyncio
import logging
import random
import os
import sys
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print version info (helps debug the AttributeError fix)
logger.info(f"Python version: {sys.version}")
logger.info(f"Telegram bot version: {__import__('telegram').__version__}")

# ---------- CONFIGURATION ----------
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN environment variable not set!")
    sys.exit(1)

GROUP_IDS_FILE = "group_ids.txt"

# ---------- LARGE POOL OF RELATED TOPICS (35 unique messages) ----------
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
    "📈 VIP interest rate just increased to 3.5% – now is the perfect time.",
    "⭐ Daily rewards are credited automatically – watch your balance grow.",
    "📊 Track your performance with real-time analytics tools.",
    "🎁 Referral contests every month – win bonus prizes!"
]

# ---------- YOUR EXACT PROMOTIONAL TEXT (sent at the end) ----------
FINAL_CALL = (
    "✅ VIP has increased to 3.5% + 3📌\n\n"
    "🪙 REGISTER HERE ⏩⏩ https://app-web.mobiuspe-app.com/regist?code=earnmoney426\n\n"
    "✅ We offer team leader salaries and up to 0.6% team commission. Please contact us to apply for a team leader position. 🛒\n\n"
    "Official channel link ⭐️ https://t.me/mobiuspayofficial1\n"
    "Contact support ⭐️ @puya1521"
)

# ---------- GROUP ID PERSISTENCE (file‑based) ----------
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

# ---------- HELPERS ----------
async def send_to_all_groups(context, text):
    for cid in load_group_ids():
        try:
            await context.bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send to {cid}: {e}")

# ---------- THE DAILY 1‑HOUR SESSION ----------
async def daily_session(context, test_mode=False):
    # Choose interval: 10 seconds for test, 4 minutes for production
    interval_seconds = 10 if test_mode else 240  # 240 = 4 minutes
    max_messages = 60 * 60 // 240  # 15 messages per hour (for production)
    
    # For test mode, we only send 4 random topics + final call
    if test_mode:
        # Pick 4 unique random messages
        shuffled = random.sample(TOPIC_POOL, min(4, len(TOPIC_POOL)))
        for msg in shuffled:
            await send_to_all_groups(context, msg)
            await asyncio.sleep(3)  # 3 seconds between test messages
        # Send final promotion
        await send_to_all_groups(context, FINAL_CALL)
        return
    
    # --- Production mode (full 1‑hour session) ---
    # Seed with today's date so the order changes daily
    today_seed = datetime.now().date().toordinal()
    random.seed(today_seed)
    shuffled = random.sample(TOPIC_POOL, len(TOPIC_POOL))
    
    # Send topic messages at 4‑minute intervals
    for i in range(min(max_messages, len(shuffled))):
        msg = shuffled[i]
        await send_to_all_groups(context, msg)
        if i < max_messages - 1:
            await asyncio.sleep(interval_seconds)
    
    # After the hour, send the FINAL CALL
    await asyncio.sleep(5)
    await send_to_all_groups(context, FINAL_CALL)
    logger.info("Daily session completed.")

# Scheduler wrapper
def start_daily_session(context):
    asyncio.create_task(daily_session(context))

# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot is active! I'll share daily insights and special offers.\n"
        "Use /test to see a quick demo right now."
    )

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
        await context.bot.send_message(
            chat_id=chat.id,
            text="🎉 Thanks for adding me! I'll post daily insights and offers at the scheduled time.\nUse /test for a quick demo."
        )

# ---------- /test COMMAND (4 topics + final call) ----------
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🧪 **Test Session Started!**\n\nI'll send 4 quick tips, followed by our main offer."
    )
    # Pick 4 random unique messages
    shuffled_topics = random.sample(TOPIC_POOL, min(4, len(TOPIC_POOL)))
    for msg in shuffled_topics:
        await context.bot.send_message(chat_id=chat_id, text=msg)
        await asyncio.sleep(3)
    # Send the final promotional call
    await context.bot.send_message(chat_id=chat_id, text=FINAL_CALL)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ **Test complete!** The daily scheduled session will run automatically at 10:00 AM UTC."
    )

# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addgroup", add_group))
    app.add_handler(CommandHandler("test", test_command))  # <-- our new test command
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_group))

    # Schedule the daily session (10:00 AM UTC every day)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        start_daily_session,
        "cron",
        hour=10,
        minute=0,
        args=[app]
    )
    scheduler.start()

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
