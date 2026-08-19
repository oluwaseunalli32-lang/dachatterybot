import asyncio
import logging
import random
import os
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- CONFIGURATION ----------
TOKEN_A = os.environ.get("BOT_TOKEN_A")
TOKEN_B = os.environ.get("BOT_TOKEN_B")
if not TOKEN_A or not TOKEN_B:
    logger.error("Both BOT_TOKEN_A and BOT_TOKEN_B must be set!")
    sys.exit(1)

GROUP_IDS_FILE = "group_ids.txt"

# ---------- CONVERSATION PAIRS ----------
CONVERSATION_PAIRS = [
    ("📊 Did you know passive income streams are growing 20% year over year?", 
     "Indeed! And our VIP plan gives you 3.5% daily – that's a game changer."),
    ("💡 The best time to start earning in crypto was yesterday, but the second best is today.", 
     "Exactly – every day you wait is lost profit. Join now and start compounding."),
    ("👥 Team leaders earn significantly more than solo players.", 
     "Yes, building a downline multiplies your rewards. We offer up to 0.6% team commission."),
    ("📈 Market volatility is your friend when you have a stable yield plan.", 
     "Our algorithm adjusts to market trends, ensuring your yield remains consistent."),
    ("🏆 Top earners in our program make 5x more by referring just 10 active users.", 
     "Referral bonuses are unlimited – the more you share, the more you earn."),
    ("⏳ Every minute you wait is a missed opportunity. The window for high yields is now.", 
     "Absolutely. The VIP rate just increased – this is the perfect moment to register."),
    ("🔐 Security first – our platform uses bank‑grade encryption for all transactions.", 
     "Your funds are safe. We also have 24/7 monitoring for extra peace of mind."),
    ("🚀 Crypto adoption is skyrocketing. Getting ahead of the curve is smart.", 
     "Our VIP members enjoy early access to new features and higher staking rewards."),
    ("🧠 Education is key – we provide daily tips to maximise your earnings.", 
     "We also have a community where you can learn from top earners every day."),
    ("💎 VIP members get priority support and exclusive bonuses.", 
     "Plus, you receive daily payouts automatically – no delays, no hassle."),
    ("📱 Our mobile dashboard lets you manage your earnings from anywhere.", 
     "It's intuitive and gives you real‑time analytics on your growth."),
    ("🔄 Compounding is the 8th wonder of the world. Our 3.5% daily return compounds fast.", 
     "In just a few months, your investment can double. It's powerful."),
    ("🤝 Community matters – join our official channel and connect with top earners.", 
     "You'll get insider tips and early announcements. Don't miss out!"),
    ("📅 We process withdrawals within 24 hours – no lock‑in periods.", 
     "You have full control over your funds. Withdraw anytime you want."),
    ("🌟 Real testimonials: 'I doubled my investment in 3 months with this program.'", 
     "That's the power of consistent daily returns. You can achieve the same."),
    ("📊 Diversify your portfolio with a stable high‑yield addition like ours.", 
     "Our track record speaks for itself. It's a smart addition to any portfolio."),
    ("⏰ The early bird gets the worm – register now before the next bonus round ends.", 
     "Yes, the current bonus period is limited. Act fast to secure the extra rewards."),
    ("🔥 Referral bonuses are unlimited – you earn even when your team grows.", 
     "That's passive income on top of your daily yield. It's a win‑win."),
    ("🏦 No hidden fees – what you see is what you earn.", 
     "Transparency is our policy. Every transaction is clearly shown in your dashboard."),
    ("📈 Our algorithm adjusts to market trends to keep your yield consistent.", 
     "It's designed to weather market fluctuations, so your returns remain stable."),
    ("💬 24/7 support team – we're here to answer all your questions.", 
     "Support is available via @puya1521 – they're friendly and responsive."),
    ("🎯 Set your daily earning goal and watch it become reality.", 
     "With our tools, you can track your progress and stay motivated."),
    ("🧩 Team commission structure is transparent – up to 0.6% for leaders.", 
     "If you're a team leader, you also receive salaries. Contact us to apply."),
    ("🌍 Our community spans 50+ countries – you're joining a global movement.", 
     "Network with like‑minded earners and share strategies."),
    ("🛡️ Risk management tools are included – protect your capital while earning.", 
     "We give you options to hedge, so you can earn with confidence."),
    ("📆 Monthly leaderboard competitions – win extra prizes for top performers.", 
     "Compete and earn recognition plus additional bonuses."),
    ("💼 Treat this as a side business – it has real income potential.", 
     "Many of our members have turned this into their primary income source."),
    ("📲 Instant notifications for every transaction – stay in control.", 
     "You'll never miss a deposit or withdrawal. Total transparency."),
    ("🔗 Share your referral link and start earning within minutes.", 
     "It's that simple – every new user brings you rewards."),
    ("🏅 Become a team leader and unlock exclusive training sessions.", 
     "We provide mentorship to help you grow your team effectively."),
    ("💸 Withdraw your earnings anytime – no lock‑in periods.", 
     "Your money is always accessible. Withdrawal requests are processed swiftly."),
]

FINAL_CALL_A = (
    "✅ VIP has increased to 3.5% + 3📌\n\n"
    "🪙 REGISTER HERE ⏩⏩ https://app-web.mobiuspe-app.com/regist?code=earnmoney426\n\n"
    "✅ We offer team leader salaries and up to 0.6% team commission. Please contact us to apply for a team leader position. 🛒\n\n"
    "Official channel link ⭐️ https://t.me/mobiuspayofficial1\n"
    "Contact support ⭐️ @puya1521"
)

FINAL_CALL_B = (
    "💬 What are you waiting for? Click the link above and start earning today!\n"
    "If you have questions, our support team @puya1521 is ready to help."
)

# ---------- GROUP ID PERSISTENCE ----------
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

async def send_to_groups(context_a, context_b, text_a, text_b=None):
    for cid in load_group_ids():
        if text_a:
            try:
                await context_a.bot.send_message(chat_id=cid, text=text_a, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Bot A failed to send to {cid}: {e}")
        if text_b:
            try:
                await context_b.bot.send_message(chat_id=cid, text=text_b, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Bot B failed to send to {cid}: {e}")

# ---------- DAILY SESSION ----------
async def daily_session(app_a, app_b, test_mode=False):
    if test_mode:
        min_wait, max_wait = 5, 10
        pairs = random.sample(CONVERSATION_PAIRS, min(3, len(CONVERSATION_PAIRS)))
    else:
        min_wait, max_wait = 60, 180
        today_seed = datetime.now().date().toordinal()
        random.seed(today_seed)
        shuffled = random.sample(CONVERSATION_PAIRS, len(CONVERSATION_PAIRS))
        pairs = shuffled[:15]

    for idx, (msg_a, msg_b) in enumerate(pairs):
        await send_to_groups(app_a, app_b, msg_a, None)
        wait = random.randint(min_wait, max_wait)
        logger.info(f"Bot A sent, waiting {wait}s for Bot B")
        await asyncio.sleep(wait)

        await send_to_groups(app_a, app_b, None, msg_b)
        if idx < len(pairs) - 1:
            wait = random.randint(min_wait, max_wait)
            logger.info(f"Bot B replied, waiting {wait}s for next pair")
            await asyncio.sleep(wait)

    await asyncio.sleep(5)
    await send_to_groups(app_a, app_b, FINAL_CALL_A, FINAL_CALL_B)
    logger.info("Daily session completed.")

def start_daily_session(app_a, app_b):
    asyncio.create_task(daily_session(app_a, app_b, test_mode=False))

# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Two‑bot system is active! We'll have a conversation about earning opportunities.\n"
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
            text="🎉 Thanks for adding us! We'll have daily conversations about earning.\nUse /test for a quick demo."
        )

# ---------- /test COMMAND ----------
async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🧪 Test session started! (3 exchanges + final)")
    
    # Get app_b from global
    global APP_B
    app_a = context.application
    app_b = APP_B
    
    pairs = random.sample(CONVERSATION_PAIRS, min(3, len(CONVERSATION_PAIRS)))
    for msg_a, msg_b in pairs:
        await app_a.bot.send_message(chat_id, msg_a)
        await asyncio.sleep(5)
        await app_b.bot.send_message(chat_id, msg_b)
        await asyncio.sleep(5)
    
    await app_a.bot.send_message(chat_id, FINAL_CALL_A)
    await asyncio.sleep(3)
    await app_b.bot.send_message(chat_id, FINAL_CALL_B)
    await context.bot.send_message(chat_id, "✅ Test complete! Daily session will run at scheduled time.")

# ---------- MAIN (Fixed) ----------
async def main():
    global APP_B
    
    # Build applications
    app_a = Application.builder().token(TOKEN_A).build()
    app_b = Application.builder().token(TOKEN_B).build()
    APP_B = app_b
    
    # Register handlers on both apps
    for app in (app_a, app_b):
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("addgroup", add_group))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_group))
    
    app_a.add_handler(CommandHandler("test", test_handler))
    
    # Initialize and start apps
    await app_a.initialize()
    await app_b.initialize()
    await app_a.start()
    await app_b.start()
    
    # Schedule daily session
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        start_daily_session,
        "cron",
        hour=10,
        minute=0,
        args=[app_a, app_b]
    )
    scheduler.start()
    
    logger.info("Both bots started. Press Ctrl+C to stop.")
    
    # Start polling for both bots
    poll_a = asyncio.create_task(app_a.updater.start_polling(allowed_updates=Update.ALL_TYPES))
    poll_b = asyncio.create_task(app_b.updater.start_polling(allowed_updates=Update.ALL_TYPES))
    
    # Wait for termination signal
    try:
        await asyncio.gather(poll_a, poll_b)
    except asyncio.CancelledError:
        logger.info("Received cancellation, stopping...")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping...")
    finally:
        # Proper shutdown sequence
        logger.info("Stopping polling...")
        await app_a.updater.stop()
        await app_b.updater.stop()
        logger.info("Stopping apps...")
        await app_a.stop()
        await app_b.stop()
        logger.info("Shutting down...")
        await app_a.shutdown()
        await app_b.shutdown()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process terminated.")
