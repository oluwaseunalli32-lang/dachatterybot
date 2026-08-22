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

# ---------- CONVERSATION PAIRS (about USDT exchange and rewards) ----------
CONVERSATION_PAIRS = [
    ("💰 USDT exchange rewards are live! Have you seen the new rates?", 
     "Yes! USDT is at 108.5 – that's a great rate to exchange right now."),
    
    ("🏆 Did you know you can earn up to ₹15,000 bonus on exchanges?", 
     "Absolutely – the more you exchange, the higher the reward. It's tiered!"),
    
    ("📊 If you exchange 100 USDT+, you get ₹80 reward instantly.", 
     "That's a nice bonus on top of the competitive rate. Every bit helps."),
    
    ("🔥 400 USDT+ gives you ₹400 – that's a 1% reward!", 
     "And it scales up – 1000 USDT gives ₹1,200, which is even better."),
    
    ("💎 Exchange 2000 USDT and get ₹3,000 reward – that's huge!", 
     "Yes, and at 4000 USDT it's ₹8,000 – the rewards keep growing."),
    
    ("🏅 The top tier: 6000 USDT+ unlocks ₹15,000 bonus! That's massive.", 
     "That's a 2.5% reward – unbeatable in today's market."),
    
    ("🔔 The official link is live: https://wallet.paisa-base.com/register?inviteCode=phar6p", 
     "I've registered already – the process is smooth and the rewards are credited quickly."),
    
    ("🤝 Invite your friends and build a team – you earn even more.", 
     "Team building is encouraged. The more active members, the better the ecosystem."),
    
    ("📩 For details, just DM @jetlee261 – they respond fast.", 
     "Yes, support is top‑notch. They'll guide you through the exchange process."),
    
    ("🚀 USDT is stable and widely used – exchanging now is a smart move.", 
     "With the bonus rewards, it's a win‑win. You get extra value for your exchange."),
    
    ("⏰ The offer is time‑limited – don't miss out on these rewards.", 
     "Exactly – early adopters get the best rates and bonuses. Act now."),
    
    ("📈 The exchange rate is competitive – 108.5 for USDT is above market.", 
     "Yes, you get more INR for your USDT compared to other platforms."),
    
    ("🎯 Set a target: exchange 6000 USDT and get ₹15,000 – that's a goal!", 
     "It's achievable if you plan your exchanges. Many users are already there."),
    
    ("💬 The community is growing – join the official channel for updates.", 
     "DM @jetlee261 for the channel link – they share exclusive tips."),
    
    ("🔄 Exchange more, earn more – that's the motto. It's simple.", 
     "Yes, the tiered structure encourages higher volumes, which benefits everyone."),
    
    ("🛡️ The platform is secure – your transactions are safe.", 
     "I've used it – no issues. It's reliable and transparent."),
    
    ("📱 You can exchange from your mobile – it's user‑friendly.", 
     "The dashboard is intuitive. You can track your rewards in real‑time."),
    
    ("💡 Did you know you can combine exchange rewards with referral bonuses?", 
     "Yes, referrals add extra income – share your invite code and earn."),
    
    ("🌟 Real users have already earned thousands – check the testimonials.", 
     "I've seen screenshots – the rewards are real and paid out promptly."),
    
    ("📆 Daily exchange limits? No – you can exchange as much as you want.", 
     "That flexibility is great for high‑volume traders."),
    
    ("📊 The reward tiers are updated regularly – stay tuned for more.", 
     "Yes, they might add higher tiers or bonuses – keep an eye out."),
    
    ("🔐 Your funds are safe – we use bank‑grade security.", 
     "That gives me confidence to exchange larger amounts."),
    
    ("📲 Instant notifications – you'll know when rewards are credited.", 
     "Yes, the system sends alerts. It's transparent and fast."),
    
    ("🤖 The registration is quick – just use the official link.", 
     "I registered in 2 minutes. The process is smooth."),
    
    ("📞 Support is available 24/7 via @jetlee261 – they're helpful.", 
     "They answered all my questions promptly. Great service."),
    
    ("🏁 Start with a small exchange to test the system – then go big.", 
     "That's a good strategy. Once you see the rewards, you'll want to exchange more."),
    
    ("💰 The reward bonus is credited instantly after exchange.", 
     "Yes, no waiting. It's automatic – you see the balance update."),
    
    ("🌍 This is a global opportunity – users from many countries are joining.", 
     "The platform is international, but INR rewards are great for Indian users."),
    
    ("📌 Bookmark the official link: https://wallet.paisa-base.com/register?inviteCode=phar6p", 
     "I've saved it – easy to access anytime."),
    
    ("🏆 The top earners are exchanging 6000+ USDT daily – they get ₹15,000 every time!", 
     "That's serious income potential. It's worth building up to that level."),
    
    ("💬 Have questions? DM @jetlee261 – they'll guide you step by step.", 
     "Yes, they even provide strategy tips to maximise your rewards."),
]

# ---------- NEW FINAL PROMOTIONAL MESSAGES (exactly as provided) ----------
FINAL_CALL_A = (
    "USDT EXCHANGE REWARDS ARE LIVE! 🔄\n\n"
    "🏆🏆🏆 USDT Rate: 1️⃣0️⃣8️⃣🔤5️⃣\n\n"
    "📌Enjoy a competitive rate while unlocking extra exchange rewards!\n\n"
    "OFFICIAL LINK : \n\n"
    "https://wallet.paisa-base.com/register?inviteCode=phar6p\n\n"
    "🔔🔔🔔Exchange More, Earn More!\n\n"
    "☄️Your rewards are waiting:\n"
    "⭐️ 100 USDT+ → ₹80 Reward\n"
    "⭐️ 400 USDT+ → ₹400 Reward\n"
    "⭐️ 1000 USDT+ → ₹1,200 Reward\n"
    "⭐️ 2000 USDT+ → ₹3,000 Reward\n"
    "⭐️ 4000 USDT+ → ₹8,000 Reward\n"
    "🏆 6000 USDT+ → ₹15,000 Reward\n"
    "✔️Unlock up to ₹15,000 bonus reward with 6000+ USDT exchange!\n"
    "🤝 Invite your friends, build your team, and start working today!\n"
    "📩 DM for details & join now!@jetlee261  ✅"
)

FINAL_CALL_B = (
    "💬 That's an amazing offer! Contact @jetlee261 right now to get started.\n"
    "Don't miss out on these rewards – exchange USDT and earn big! 🚀"
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

# ---------- DAILY 1‑HOUR SESSION ----------
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
        "🤖 USDT Exchange Rewards Bot is active!\n"
        "We'll talk about exchange opportunities and rewards.\n"
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
            text="🎉 Thanks for adding us! We'll share insights on USDT exchange rewards.\nUse /test for a quick demo."
        )

# ---------- /test COMMAND ----------
async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🧪 Test session started! (3 exchanges + final)")
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

# ---------- MAIN (Always online, auto‑restart polling) ----------
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
    
    # Keep bots running; restart polling if it stops
    while True:
        try:
            await asyncio.gather(
                app_a.updater.start_polling(allowed_updates=Update.ALL_TYPES),
                app_b.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            )
            logger.warning("Polling stopped unexpectedly. Restarting in 5 seconds...")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Cancellation received, shutting down...")
            break
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
            logger.info("Restarting polling in 10 seconds...")
            await asyncio.sleep(10)
            continue
    
    # Clean shutdown
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
