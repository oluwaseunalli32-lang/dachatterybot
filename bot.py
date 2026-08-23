import asyncio
import logging
import os
import random
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

TOKEN_A = os.environ.get("BOT_TOKEN_A")
TOKEN_B = os.environ.get("BOT_TOKEN_B")

if not TOKEN_A or not TOKEN_B:
    raise RuntimeError(
        "BOT_TOKEN_A and BOT_TOKEN_B must both be set."
    )

GROUP_IDS_FILE = Path("group_ids.txt")

APP_A = None
APP_B = None


# =========================================================
# SESSION SETTINGS
# =========================================================

SESSION_INTERVAL = 3 * 60 * 60  # 3 hours

TEST_WAIT = 5

# Each group gets its own running task.
GROUP_SESSION_TASKS = {}

# Prevents multiple sessions from running in the same group.
GROUP_LOCKS = {}


# =========================================================
# REAL PROMOTIONAL CONVERSATION
# =========================================================

CONVERSATION_PAIRS = [
    (
        "💰 USDT exchange rewards are live! Have you seen the new rates?",
        "Yes! USDT is at 108.5 – that's a great rate to exchange right now.",
    ),
    (
        "🏆 Did you know you can earn up to ₹15,000 bonus on exchanges?",
        "Absolutely – the more you exchange, the higher the reward. It's tiered!",
    ),
    (
        "📊 If you exchange 100 USDT+, you get ₹80 reward instantly.",
        "That's a nice bonus on top of the competitive rate. Every bit helps.",
    ),
    (
        "🔥 400 USDT+ gives you ₹400 – that's a 1% reward!",
        "And it scales up – 1000 USDT gives ₹1,200, which is even better.",
    ),
    (
        "💎 Exchange 2000 USDT and get ₹3,000 reward – that's huge!",
        "Yes, and at 4000 USDT it's ₹8,000 – the rewards keep growing.",
    ),
    (
        "🏅 The top tier: 6000 USDT+ unlocks ₹15,000 bonus! That's massive.",
        "That's a 2.5% reward – unbeatable in today's market.",
    ),
    (
        "🔔 The official link is live: https://wallet.paisa-base.com/register?inviteCode=phar6p",
        "I've registered already – the process is smooth and the rewards are credited quickly.",
    ),
    (
        "🤝 Invite your friends and build a team – you earn even more.",
        "Team building is encouraged. The more active members, the better the ecosystem.",
    ),
    (
        "📩 For details, just DM @jetlee261 – they respond fast.",
        "Yes, support is top‑notch. They'll guide you through the exchange process.",
    ),
    (
        "🚀 USDT is stable and widely used – exchanging now is a smart move.",
        "With the bonus rewards, it's a win‑win. You get extra value for your exchange.",
    ),
    (
        "⏰ The offer is time‑limited – don't miss out on these rewards.",
        "Exactly – early adopters get the best rates and bonuses. Act now.",
    ),
    (
        "📈 The exchange rate is competitive – 108.5 for USDT is above market.",
        "Yes, you get more INR for your USDT compared to other platforms.",
    ),
    (
        "🎯 Set a target: exchange 6000 USDT and get ₹15,000 – that's a goal!",
        "It's achievable if you plan your exchanges. Many users are already there.",
    ),
    (
        "💬 The community is growing – join the official channel for updates.",
        "DM @jetlee261 for the channel link – they share exclusive tips.",
    ),
    (
        "🔄 Exchange more, earn more – that's the motto. It's simple.",
        "Yes, the tiered structure encourages higher volumes, which benefits everyone.",
    ),
    (
        "🛡️ The platform is secure – your transactions are safe.",
        "I've used it – no issues. It's reliable and transparent.",
    ),
    (
        "📱 You can exchange from your mobile – it's user‑friendly.",
        "The dashboard is intuitive. You can track your rewards in real‑time.",
    ),
    (
        "💡 Did you know you can combine exchange rewards with referral bonuses?",
        "Yes, referrals add extra income – share your invite code and earn.",
    ),
    (
        "🌟 Real users have already earned thousands – check the testimonials.",
        "I've seen screenshots – the rewards are real and paid out promptly.",
    ),
    (
        "📆 Daily exchange limits? No – you can exchange as much as you want.",
        "That flexibility is great for high‑volume traders.",
    ),
    (
        "📊 The reward tiers are updated regularly – stay tuned for more.",
        "Yes, they might add higher tiers or bonuses – keep an eye out.",
    ),
    (
        "🔐 Your funds are safe – we use bank‑grade security.",
        "That gives me confidence to exchange larger amounts.",
    ),
    (
        "📲 Instant notifications – you'll know when rewards are credited.",
        "Yes, the system sends alerts. It's transparent and fast.",
    ),
    (
        "🤖 The registration is quick – just use the official link.",
        "I registered in 2 minutes. The process is smooth.",
    ),
    (
        "📞 Support is available 24/7 via @jetlee261 – they're helpful.",
        "They answered all my questions promptly. Great service.",
    ),
    (
        "🏁 Start with a small exchange to test the system – then go big.",
        "That's a good strategy. Once you see the rewards, you'll want to exchange more.",
    ),
    (
        "💰 The reward bonus is credited instantly after exchange.",
        "Yes, no waiting. It's automatic – you see the balance update.",
    ),
    (
        "🌍 This is a global opportunity – users from many countries are joining.",
        "The platform is international, but INR rewards are great for Indian users.",
    ),
    (
        "📌 Bookmark the official link: https://wallet.paisa-base.com/register?inviteCode=phar6p",
        "I've saved it – easy to access anytime.",
    ),
    (
        "🏆 The top earners are exchanging 6000+ USDT daily – they get ₹15,000 every time!",
        "That's serious income potential. It's worth building up to that level.",
    ),
    (
        "💬 Have questions? DM @jetlee261 – they'll guide you step by step.",
        "Yes, they even provide strategy tips to maximise your rewards.",
    ),
]


# =========================================================
# FINAL / CTA MESSAGES
# =========================================================

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


# =========================================================
# GROUP ID STORAGE
# =========================================================

def load_group_ids():
    """Load saved group IDs."""

    if not GROUP_IDS_FILE.exists():
        return []

    group_ids = []

    try:
        with GROUP_IDS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    group_ids.append(int(line))

                except ValueError:
                    logger.warning(
                        "Ignoring invalid group ID: %s",
                        line,
                    )

    except OSError as error:
        logger.error(
            "Could not read group ID file: %s",
            error,
        )

    return group_ids


def save_group_id(chat_id):
    """Save a group ID if it does not already exist."""

    group_ids = load_group_ids()

    if chat_id in group_ids:
        return

    group_ids.append(chat_id)

    try:
        with GROUP_IDS_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            for group_id in group_ids:
                file.write(f"{group_id}\n")

        logger.info(
            "Saved group ID: %s",
            chat_id,
        )

    except OSError as error:
        logger.error(
            "Could not save group ID %s: %s",
            chat_id,
            error,
        )


# =========================================================
# GROUP LOCK
# =========================================================

def get_group_lock(chat_id):
    """Return the asyncio lock for a specific group."""

    if chat_id not in GROUP_LOCKS:
        GROUP_LOCKS[chat_id] = asyncio.Lock()

    return GROUP_LOCKS[chat_id]


# =========================================================
# SEND TO BOTH BOTS
# =========================================================

async def send_bot_a(chat_id, text):
    """Send a message through Bot A."""

    if APP_A is None:
        logger.error("Bot A is not initialized.")
        return None

    try:
        message = await APP_A.bot.send_message(
            chat_id=chat_id,
            text=text,
        )

        logger.info(
            "Bot A sent message to %s",
            chat_id,
        )

        return message

    except Exception as error:
        logger.error(
            "Bot A failed to send to %s: %s",
            chat_id,
            error,
        )

        return None


async def send_bot_b(chat_id, text):
    """Send a message through Bot B."""

    if APP_B is None:
        logger.error("Bot B is not initialized.")
        return None

    try:
        message = await APP_B.bot.send_message(
            chat_id=chat_id,
            text=text,
        )

        logger.info(
            "Bot B sent message to %s",
            chat_id,
        )

        return message

    except Exception as error:
        logger.error(
            "Bot B failed to send to %s: %s",
            chat_id,
            error,
        )

        return None


# =========================================================
# ONE SESSION
# =========================================================

async def run_session(chat_id, test_mode=False):
    """
    Run exactly one conversation session.

    This function does NOT schedule the next session.
    The caller handles the 3-hour delay.
    """

    logger.info(
        "Starting session for group %s",
        chat_id,
    )

    if test_mode:
        # Use fewer pairs for test
        pairs = random.sample(
            CONVERSATION_PAIRS,
            min(3, len(CONVERSATION_PAIRS)),
        )
        wait_min, wait_max = 5, 10
    else:
        # Use up to 15 pairs for a balanced session
        pairs = random.sample(
            CONVERSATION_PAIRS,
            min(15, len(CONVERSATION_PAIRS)),
        )
        wait_min, wait_max = 60, 180  # 1‑3 minutes

    for index, (message_a, message_b) in enumerate(pairs):

        # ---------------------------------------------
        # BOT A
        # ---------------------------------------------

        await send_bot_a(
            chat_id,
            message_a,
        )

        # ---------------------------------------------
        # WAIT
        # ---------------------------------------------

        wait_time = random.randint(wait_min, wait_max)
        logger.info(
            "Waiting %s seconds before Bot B replies.",
            wait_time,
        )
        await asyncio.sleep(wait_time)

        # ---------------------------------------------
        # BOT B
        # ---------------------------------------------

        await send_bot_b(
            chat_id,
            message_b,
        )

        # ---------------------------------------------
        # WAIT BEFORE NEXT PAIR
        # ---------------------------------------------

        if index < len(pairs) - 1:

            wait_time = random.randint(wait_min, wait_max)
            logger.info(
                "Waiting %s seconds before next pair.",
                wait_time,
            )
            await asyncio.sleep(wait_time)

    # =====================================================
    # FINAL SESSION MESSAGE
    # =====================================================

    await asyncio.sleep(5)

    await send_bot_a(
        chat_id,
        FINAL_CALL_A,
    )

    await asyncio.sleep(3)

    await send_bot_b(
        chat_id,
        FINAL_CALL_B,
    )

    logger.info(
        "Session completed for group %s",
        chat_id,
    )


# =========================================================
# CONTINUOUS 3-HOUR SESSION
# =========================================================

async def group_session_loop(chat_id):
    """
    Run: session → final CTA → wait 3 hours → session → repeat.
    """

    logger.info(
        "3-hour session loop started for group %s",
        chat_id,
    )

    lock = get_group_lock(chat_id)

    try:

        # =================================================
        # FIRST SESSION
        # =================================================

        async with lock:

            await run_session(
                chat_id,
                test_mode=False,
            )

        # =================================================
        # REPEAT FOREVER
        # =================================================

        while True:

            logger.info(
                "Session finished for %s. Waiting 3 hours.",
                chat_id,
            )

            await asyncio.sleep(SESSION_INTERVAL)

            # ---------------------------------------------
            # NEXT SESSION
            # ---------------------------------------------

            async with lock:

                await run_session(
                    chat_id,
                    test_mode=False,
                )

    except asyncio.CancelledError:

        logger.info(
            "Session loop cancelled for group %s",
            chat_id,
        )

        raise

    except Exception as error:

        logger.exception(
            "Session loop failed for %s: %s",
            chat_id,
            error,
        )

    finally:

        GROUP_SESSION_TASKS.pop(
            chat_id,
            None,
        )

        logger.info(
            "Session loop stopped for group %s",
            chat_id,
        )


# =========================================================
# START SESSION FOR GROUP
# =========================================================

async def start_group_session(chat_id):
    """
    Start the 3-hour session loop if it isn't already running.
    """

    existing_task = GROUP_SESSION_TASKS.get(chat_id)

    if existing_task:

        if not existing_task.done():

            return False

    task = asyncio.create_task(
        group_session_loop(chat_id)
    )

    GROUP_SESSION_TASKS[chat_id] = task

    return True


# =========================================================
# STOP SESSION FOR GROUP
# =========================================================

async def stop_group_session(chat_id):
    """Stop the running session loop for a group."""

    task = GROUP_SESSION_TASKS.get(chat_id)

    if not task:
        return False

    if task.done():

        GROUP_SESSION_TASKS.pop(
            chat_id,
            None,
        )

        return False

    task.cancel()

    try:
        await task

    except asyncio.CancelledError:
        pass

    GROUP_SESSION_TASKS.pop(
        chat_id,
        None,
    )

    return True


# =========================================================
# /START
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    # ---------------------------------------------
    # Only allow groups
    # ---------------------------------------------

    if chat.type not in (
        "group",
        "supergroup",
    ):

        if update.message:

            await update.message.reply_text(
                "❌ Please use /start inside a group."
            )

        return

    chat_id = chat.id

    # ---------------------------------------------
    # Save group
    # ---------------------------------------------

    save_group_id(chat_id)

    # ---------------------------------------------
    # Start session
    # ---------------------------------------------

    started = await start_group_session(
        chat_id
    )

    if started:

        if update.message:

            await update.message.reply_text(
                "✅ Session started.\n\n"
                "The first session is running now.\n"
                "After the session finishes, the 3-hour "
                "countdown will begin."
            )

    else:

        if update.message:

            await update.message.reply_text(
                "ℹ️ A session is already running "
                "for this group."
            )


# =========================================================
# /STOP
# =========================================================

async def stop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    chat_id = chat.id

    stopped = await stop_group_session(
        chat_id
    )

    if update.message:

        if stopped:

            await update.message.reply_text(
                "🛑 Session cycle stopped."
            )

        else:

            await update.message.reply_text(
                "ℹ️ No active session was running."
            )


# =========================================================
# /TEST
# =========================================================

async def test_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in (
        "group",
        "supergroup",
    ):

        if update.message:

            await update.message.reply_text(
                "❌ Please use /test inside a group."
            )

        return

    chat_id = chat.id

    # ---------------------------------------------
    # Don't allow test to overlap with normal cycle
    # ---------------------------------------------

    existing_task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if existing_task and not existing_task.done():

        if update.message:

            await update.message.reply_text(
                "⚠️ A normal session is already running "
                "for this group."
            )

        return

    if update.message:

        await update.message.reply_text(
            "🧪 Test session starting..."
        )

    try:

        await run_session(
            chat_id,
            test_mode=True,
        )

        if update.message:

            await update.message.reply_text(
                "✅ Test session completed."
            )

    except Exception as error:

        logger.exception(
            "Test session failed: %s",
            error,
        )

        if update.message:

            await update.message.reply_text(
                "❌ Test session failed. "
                "Check the bot logs."
            )


# =========================================================
# /STATUS
# =========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    chat_id = chat.id

    task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if task and not task.done():

        status = (
            "🟢 ACTIVE\n\n"
            "The session cycle is running.\n"
            "After each completed session, "
            "the bot waits 3 hours before starting "
            "the next one."
        )

    else:

        status = (
            "🔴 INACTIVE\n\n"
            "No session cycle is currently running.\n"
            "Use /start to begin."
        )

    if update.message:

        await update.message.reply_text(
            status
        )


# =========================================================
# /ADDGROUP
# =========================================================

async def add_group_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in (
        "group",
        "supergroup",
    ):

        if update.message:

            await update.message.reply_text(
                "❌ This command must be used inside a group."
            )

        return

    save_group_id(
        chat.id
    )

    if update.message:

        await update.message.reply_text(
            "✅ This group has been registered."
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )


# =========================================================
# ADD HANDLERS
# =========================================================

def configure_application(application):
    """Add the same commands to a bot."""

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "stop",
            stop_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "test",
            test_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "addgroup",
            add_group_command,
        )
    )

    application.add_error_handler(
        error_handler
    )


# =========================================================
# MAIN (FIXED: concurrent polling)
# =========================================================

async def main():

    global APP_A
    global APP_B

    logger.info("========================================")
    logger.info("STARTING TWO-BOT SYSTEM")
    logger.info("========================================")

    # =====================================================
    # CREATE BOT A
    # =====================================================

    APP_A = (
        Application.builder()
        .token(TOKEN_A)
        .build()
    )

    configure_application(APP_A)

    # =====================================================
    # CREATE BOT B
    # =====================================================

    APP_B = (
        Application.builder()
        .token(TOKEN_B)
        .build()
    )

    configure_application(APP_B)

    # =====================================================
    # INITIALIZE
    # =====================================================

    logger.info("Initializing Bot A...")
    await APP_A.initialize()

    logger.info("Initializing Bot B...")
    await APP_B.initialize()

    # =====================================================
    # REMOVE WEBHOOKS
    # =====================================================

    logger.info("Removing Bot A webhook...")
    await APP_A.bot.delete_webhook(
        drop_pending_updates=True
    )

    logger.info("Removing Bot B webhook...")
    await APP_B.bot.delete_webhook(
        drop_pending_updates=True
    )

    # =====================================================
    # START APPLICATIONS
    # =====================================================

    await APP_A.start()
    await APP_B.start()

    logger.info("Both applications started.")

    # =====================================================
    # START POLLING FOR BOTH BOTS CONCURRENTLY
    # =====================================================

    try:

        logger.info("Starting polling for both bots...")

        # ✅ FIX: run both polling tasks concurrently
        await asyncio.gather(

            APP_A.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            ),

            APP_B.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            ),

        )

        # This line is only reached if polling stops (unlikely)
        logger.warning("Polling stopped unexpectedly.")

    except asyncio.CancelledError:

        logger.info("Shutdown requested.")

    finally:

        # =================================================
        # STOP ALL GROUP SESSIONS
        # =================================================

        logger.info("Stopping all active group sessions...")

        tasks = list(GROUP_SESSION_TASKS.values())

        for task in tasks:

            if not task.done():

                task.cancel()

        if tasks:

            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        GROUP_SESSION_TASKS.clear()

        # =================================================
        # STOP POLLING
        # =================================================

        if APP_A is not None and APP_A.updater is not None and APP_A.updater.running:

            logger.info("Stopping Bot A polling...")
            await APP_A.updater.stop()

        if APP_B is not None and APP_B.updater is not None and APP_B.updater.running:

            logger.info("Stopping Bot B polling...")
            await APP_B.updater.stop()

        # =================================================
        # STOP APPLICATIONS
        # =================================================

        if APP_A is not None:

            logger.info("Stopping Bot A...")
            await APP_A.stop()

        if APP_B is not None:

            logger.info("Stopping Bot B...")
            await APP_B.stop()

        # =================================================
        # SHUTDOWN
        # =================================================

        if APP_A is not None:

            logger.info("Shutting down Bot A...")
            await APP_A.shutdown()

        if APP_B is not None:

            logger.info("Shutting down Bot B...")
            await APP_B.shutdown()

        logger.info("========================================")
        logger.info("BOT SYSTEM SHUTDOWN COMPLETE")
        logger.info("========================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info("Bot stopped manually.")

    except Exception as error:

        logger.exception(
            "Fatal error: %s",
            error,
        )
