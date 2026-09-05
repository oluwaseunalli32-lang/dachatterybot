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


# =========================================================
# GLOBAL APPLICATION REFERENCES
# =========================================================

APP_A = None
APP_B = None


# =========================================================
# SESSION SETTINGS
# =========================================================

# 3 hours
SESSION_INTERVAL = 3 * 60 * 60

# Normal session message delay
NORMAL_WAIT_MIN = 10
NORMAL_WAIT_MAX = 30

# Test session message delay
TEST_WAIT_MIN = 3
TEST_WAIT_MAX = 5


# =========================================================
# ACTIVE GROUP TASKS
# =========================================================

GROUP_SESSION_TASKS = {}


# =========================================================
# SESSION CONTENT POOL (5 different session types)
# =========================================================

SESSION_CONTENT = [
    {
        "name": "Spin & Win",
        "pairs": [
            (
                "🔔🔥 SPIN & WIN BIG! Have you seen the Lucky Wheel rewards?",
                "Yes! 100% win rate – everyone gets a reward. Complete tasks to earn spins!",
            ),
            (
                "🎡 Complete tasks → Earn spin chances. Spin the Lucky Wheel → Get rewards instantly!",
                "More tasks. More spins. More chances to win. 🏆",
            ),
            (
                "💙 Join Paisabase and try your luck today! Everyone gets a reward!",
                "The more you spin, the more you win. Start completing tasks now!",
            ),
        ],
        "final_a": (
            "🔔 🔥🔥 SPIN & WIN BIG WITH 🔤🔤🔤🔤🔤🔤🔤🔤🔤❗️🔔 🔥🔥\n\n"
            "🗺Want more rewards? Start completing tasks now! 🚀\n\n"
            "1️⃣ Complete tasks → Earn spin chances‼️\n"
            "2️⃣ Spin the Lucky Wheel → Get rewards instantly🆕\n\n"
            "🔝 100% Win Rate! Everyone gets a reward!\n\n"
            "🛒🛒🛒More tasks. More spins. More chances to win. 🏆🏆🏆\n\n"
            "💙 Join Paisabase and try your luck today!🔜\n\n"
            "https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
        "final_b": (
            "🎡 SPIN THE WHEEL & WIN BIG!\n\n"
            "Every spin gives you a reward. Complete tasks to earn more spins.\n\n"
            "🔝 100% WIN RATE – NO ONE LOSES!\n\n"
            "Start now: https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
    },
    {
        "name": "Upgrade Level",
        "pairs": [
            (
                "🚀 Upgrade Your Level! Unlock more benefits with PaisaBase.",
                "Standard members get 3.5% commission, Premium members get 4.3%!",
            ),
            (
                "🏆 Premium Membership unlocks after ₹30,00,000 trade volume within 30 days.",
                "Every order you complete brings you one step closer to Premium!",
            ),
            (
                "📈 Reach Premium and unlock higher commission rates today!",
                "Start growing your volume now – Premium is within reach.",
            ),
        ],
        "final_a": (
            "🚀 Upgrade Your Level. Unlock More Benefits! 🚀\n\n"
            "https://wallet.paisa-base.com/register?inviteCode=phar6p\n\n"
            "🙂Standard Member↗️\n"
            "• Commission Rate: 3.5%🪙\n"
            "• Perfect for getting started and growing your trading volume.🌈\n\n"
            "▶️ Premium Member🏆\n"
            "• Commission Rate: 4.3%📈\n"
            "• Unlock after achieving ₹30,00,000 INR trade volume (excluding USDT) within 30 days.☄️\n\n"
            "😎 Every order you complete brings you one step closer to Premium Membership.🪙\n\n"
            "🛒 Start today. Grow your volume. Reach Premium🗺"
        ),
        "final_b": (
            "💎 Premium Membership unlocks higher commissions!\n\n"
            "📈 3.5% → 4.3% commission rate.\n\n"
            "🏆 Achieve ₹30,00,000 trade volume in 30 days.\n\n"
            "Start now: https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
    },
    {
        "name": "Hiring Agents",
        "pairs": [
            (
                "⚡️ WE ARE HIRING AGENTS & INFLUENCERS! Build your team and earn passive income.",
                "Earn 0.3% from Level 1, 0.1% from Level 2 – no salary limit!",
            ),
            (
                "💎 If your Team A deposits 1 Crore, you earn ₹30,000 commission.",
                "If Team B deposits 1 Crore, you earn ₹10,000 – total ₹40,000 weekly!",
            ),
            (
                "🤝 Invite friends, influencers, traders, and social media users to join your team.",
                "Bigger team = bigger income. Start building your downline today!",
            ),
        ],
        "final_a": (
            "⚡️ WE ARE HIRING AGENTS & INFLUENCERS ⚡️\n\n"
            "Build your own team and create a powerful passive income with PaisaBase! 👈\n\n"
            "✔ Earn 0.3% commission from Level 1 team\n"
            "✔ Earn 0.1% commission from Level 2 team\n"
            "✔ No salary limit — bigger team = bigger income\n\n"
            "🪧 Example:\n"
            "✨ If your Team A deposits 1 Crore, you earn ₹30,000 commission.\n"
            "✨ If your Team B deposits 1 Crore, you earn ₹10,000 commission.\n"
            "✨ Total Weekly Commission = ₹40,000\n\n"
            "Invite friends, influencers, traders, and social media users to join your team and grow together👍\n\n"
            "📤Official link:https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
        "final_b": (
            "🤝 JOIN THE PAISABASE TEAM!\n\n"
            "💰 Earn passive income with 2‑level commissions.\n\n"
            "📈 No salary limit – the bigger your team, the more you earn.\n\n"
            "Start building your team: https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
    },
    {
        "name": "Why PaisaBase",
        "pairs": [
            (
                "⚡️ Why Thousands Are Choosing PaisaBase? Personal transactions are NOT debited.",
                "Set your own selling limit, buy via Mobikwik/Freecharge, sell in round figures.",
            ),
            (
                "💳 Other app transactions are NOT debited – your money stays yours.",
                "Sell tokens in round figures like 999.56 → 1000. Simple and transparent.",
            ),
            (
                "📱 HR Contact @jetlee261 for any questions about PaisaBase.",
                "They provide quick support and guide you through the process.",
            ),
        ],
        "final_a": (
            "⚡️Why Thousands Are Choosing Paisabase⚡️\n\n"
            "📤 Official link: https://wallet.paisa-base.com/register?inviteCode=phar6p\n\n"
            "➡️ Personal transactions are NOT debited.\n"
            "➡️ Other app transactions are NOT debited.\n"
            "➡️ Set Your Own Selling Limit.\n"
            "➡️ Buying Tools Mobikwik and Freecharge.\n"
            "➡️ Sell token in round figure 999.56 🔠 1000 ✅\n\n"
            "💭\n\n"
            "📱 HR Contact: 🎉@jetlee261"
        ),
        "final_b": (
            "💎 PAISABASE – THE SMART CHOICE\n\n"
            "✅ No hidden debits\n"
            "✅ Set your own selling limit\n"
            "✅ Buy via Mobikwik / Freecharge\n"
            "✅ Sell in round figures\n\n"
            "Join now: https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
    },
    {
        "name": "USDT Rate Boost",
        "pairs": [
            (
                "🔥🔥 BIG NEWS! USDT rate just got boosted! 1 USDT = 109 INR now!",
                "💥 Exchange more, earn more: up to ₹15,000 bonus on 6000+ USDT!",
            ),
            (
                "💰 100 USDT → ₹80 Bonus | 400 USDT → ₹400 Bonus | 1000 USDT → ₹1,200 Bonus",
                "2000 USDT → ₹3,000 Bonus | 4000 USDT → ₹8,000 Bonus | 6000 USDT → ₹15,000 Bonus!",
            ),
            (
                "🔜 Don't wait for tomorrow. Boost your USDT. Boost your earnings today!",
                "Orders are moving fast, selling is instant, rewards are waiting for you!",
            ),
        ],
        "final_a": (
            "🔥🔥🔥BIG NEWS! USDT RATE JUST GOT BOOSTED! 🆕\n\n"
            "🌈🔤🔤🔤🔤🔤🔤🔤🔤🔤 brings you a bigger earning opportunity! 🚀\n\n"
            "🚨NOW 1 USDT = 109 INR 💎\n\n"
            "💥 100 USDT → ₹80 Bonus 💥400 USDT → ₹400 Bonus 💥1,000 USDT → ₹1,200 Bonus 💥2,000 USDT → ₹3,000 Bonus 💥4,000 USDT → ₹8,000 Bonus 🏆6,000 USDT → ₹15,000 Bonus🛒\n\n"
            "🤫The more USDT you exchange, the more bonus you unlock! 💰\n\n"
            "🔝From ₹80 bonus to a massive ₹15,000 reward — your next big earning opportunity is here! 🎁\n\n"
            "⚡Orders are moving fast 💱Selling is instant 🚩Rewards are waiting for you\n\n"
            "🔜Don't wait for tomorrow. Boost your USDT. Boost your earnings. 💥\n\n"
            "https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
        "final_b": (
            "💎 USDT RATE BOOSTED TO 109 INR!\n\n"
            "💰 Earn up to ₹15,000 bonus on USDT exchanges!\n\n"
            "📈 Exchange more. Earn more. Unlock bigger rewards.\n\n"
            "Start now: https://wallet.paisa-base.com/register?inviteCode=phar6p"
        ),
    },
]


# =========================================================
# GROUP ID STORAGE
# =========================================================

def load_group_ids():
    """Load saved group IDs from disk."""

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
# BOT A SENDER
# =========================================================

async def send_bot_a(
    chat_id,
    text,
):
    """Send a message using Bot A."""

    if APP_A is None:
        logger.error(
            "Bot A is not initialized."
        )
        return False

    try:

        await APP_A.bot.send_message(
            chat_id=chat_id,
            text=text,
        )

        logger.info(
            "Bot A sent message to %s",
            chat_id,
        )

        return True

    except Exception as error:

        logger.error(
            "Bot A failed to send to %s: %s",
            chat_id,
            error,
        )

        return False


# =========================================================
# BOT B SENDER
# =========================================================

async def send_bot_b(
    chat_id,
    text,
):
    """Send a message using Bot B."""

    if APP_B is None:
        logger.error(
            "Bot B is not initialized."
        )
        return False

    try:

        await APP_B.bot.send_message(
            chat_id=chat_id,
            text=text,
        )

        logger.info(
            "Bot B sent message to %s",
            chat_id,
        )

        return True

    except Exception as error:

        logger.error(
            "Bot B failed to send to %s: %s",
            chat_id,
            error,
        )

        return False


# =========================================================
# ONE SESSION
# =========================================================

async def run_session(
    chat_id,
    test_mode=False,
):
    """
    Run exactly one session.

    IMPORTANT:
    This function does NOT start the 3-hour timer.

    The caller starts the timer only after this
    function has completely finished.
    """

    logger.info(
        "========================================"
    )

    logger.info(
        "SESSION STARTED | GROUP %s | TEST=%s",
        chat_id,
        test_mode,
    )

    logger.info(
        "========================================"
    )

    # -----------------------------------------------------
    # SELECT A RANDOM CONTENT SET FOR THIS SESSION
    # -----------------------------------------------------

    content_set = random.choice(SESSION_CONTENT)
    logger.info("Session topic: %s", content_set["name"])

    # -----------------------------------------------------
    # SELECT MESSAGES FROM THE CHOSEN SET
    # -----------------------------------------------------

    if test_mode:

        number_of_pairs = min(
            2,
            len(content_set["pairs"]),
        )

        wait_min = TEST_WAIT_MIN
        wait_max = TEST_WAIT_MAX

    else:

        number_of_pairs = len(content_set["pairs"])

        wait_min = NORMAL_WAIT_MIN
        wait_max = NORMAL_WAIT_MAX

    pairs = random.sample(
        content_set["pairs"],
        number_of_pairs,
    )

    # -----------------------------------------------------
    # RUN CONVERSATION
    # -----------------------------------------------------

    for index, (
        message_a,
        message_b,
    ) in enumerate(pairs):

        # ================================================
        # BOT A
        # ================================================

        await send_bot_a(
            chat_id,
            message_a,
        )

        # ================================================
        # WAIT
        # ================================================

        wait_time = random.randint(
            wait_min,
            wait_max,
        )

        logger.info(
            "Group %s: waiting %s seconds before Bot B.",
            chat_id,
            wait_time,
        )

        await asyncio.sleep(
            wait_time
        )

        # ================================================
        # BOT B
        # ================================================

        await send_bot_b(
            chat_id,
            message_b,
        )

        # ================================================
        # WAIT BEFORE NEXT PAIR
        # ================================================

        if index < len(pairs) - 1:

            wait_time = random.randint(
                wait_min,
                wait_max,
            )

            logger.info(
                "Group %s: waiting %s seconds before next pair.",
                chat_id,
                wait_time,
            )

            await asyncio.sleep(
                wait_time
            )

    # =====================================================
    # FINAL SESSION MESSAGES
    # =====================================================

    logger.info(
        "Group %s: sending final session messages.",
        chat_id,
    )

    # Bot A sends the main CTA
    await send_bot_a(
        chat_id,
        content_set["final_a"],
    )

    await asyncio.sleep(5)

    # Bot B sends the follow-up CTA
    await send_bot_b(
        chat_id,
        content_set["final_b"],
    )

    # =====================================================
    # SESSION COMPLETELY FINISHED
    # =====================================================

    logger.info(
        "========================================"
    )

    logger.info(
        "SESSION COMPLETED | GROUP %s",
        chat_id,
    )

    logger.info(
        "3-hour countdown can now begin."
    )

    logger.info(
        "========================================"
    )


# =========================================================
# RECURRING GROUP SESSION
# =========================================================

async def group_session_loop(
    chat_id,
):
    """
    Correct timing:

        /start
           ↓
        Session 1 (random content)
           ↓
        Final CTA/message
           ↓
        3-hour wait
           ↓
        Session 2 (random content)
           ↓
        Final CTA/message
           ↓
        3-hour wait
           ↓
        repeat
    """

    logger.info(
        "Starting recurring cycle for group %s",
        chat_id,
    )

    try:

        # =================================================
        # FIRST SESSION
        # =================================================

        await run_session(
            chat_id,
            test_mode=False,
        )

        # =================================================
        # REPEAT
        # =================================================

        while True:

            # -------------------------------------------------
            # IMPORTANT:
            # The 3-hour countdown starts HERE.
            #
            # run_session() has already completely finished,
            # including FINAL_CALL_A and FINAL_CALL_B.
            # -------------------------------------------------

            logger.info(
                "Group %s: session finished.",
                chat_id,
            )

            logger.info(
                "Group %s: starting 3-hour countdown.",
                chat_id,
            )

            await asyncio.sleep(
                SESSION_INTERVAL
            )

            # -------------------------------------------------
            # NEXT SESSION (new random content)
            # -------------------------------------------------

            logger.info(
                "Group %s: 3-hour countdown completed.",
                chat_id,
            )

            await run_session(
                chat_id,
                test_mode=False,
            )

    except asyncio.CancelledError:

        logger.info(
            "Recurring cycle cancelled for group %s",
            chat_id,
        )

        raise

    except Exception as error:

        logger.exception(
            "Recurring cycle failed for group %s: %s",
            chat_id,
            error,
        )

    finally:

        current_task = asyncio.current_task()

        if (
            GROUP_SESSION_TASKS.get(chat_id)
            is current_task
        ):
            GROUP_SESSION_TASKS.pop(
                chat_id,
                None,
            )

        logger.info(
            "Recurring cycle stopped for group %s",
            chat_id,
        )


# =========================================================
# START GROUP SESSION
# =========================================================

def start_group_session(
    chat_id,
):
    """
    Start a recurring group session.

    Returns:
        True  = started
        False = already running
    """

    existing_task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if existing_task:

        if not existing_task.done():

            return False

    task = asyncio.create_task(
        group_session_loop(
            chat_id
        )
    )

    GROUP_SESSION_TASKS[chat_id] = task

    logger.info(
        "Created session task for group %s",
        chat_id,
    )

    return True


# =========================================================
# STOP GROUP SESSION
# =========================================================

async def stop_group_session(
    chat_id,
):
    """
    Stop a group's recurring session.
    """

    task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if task is None:
        return False

    if task.done():

        GROUP_SESSION_TASKS.pop(
            chat_id,
            None,
        )

        return False

    logger.info(
        "Cancelling session for group %s",
        chat_id,
    )

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
# COMMAND HANDLERS
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Start the recurring cycle for this group."""

    chat = update.effective_chat

    if chat is None:
        return

    # -----------------------------------------------------
    # GROUP ONLY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SAVE GROUP
    # -----------------------------------------------------

    save_group_id(
        chat_id
    )

    # -----------------------------------------------------
    # START CYCLE
    # -----------------------------------------------------

    started = start_group_session(
        chat_id
    )

    if started:

        if update.message:

            await update.message.reply_text(
                "✅ Session cycle started.\n\n"
                "The first promotional session will begin now.\n"
                "The 3-hour countdown starts only after "
                "the session completely finishes."
            )

    else:

        if update.message:

            await update.message.reply_text(
                "ℹ️ A session cycle is already active "
                "in this group."
            )


async def stop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Stop the recurring cycle."""

    chat = update.effective_chat

    if chat is None:
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
                "ℹ️ No active session cycle was found."
            )


async def test_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Run one promotional test session.

    This does NOT activate the 3-hour recurring cycle.
    """

    chat = update.effective_chat

    if chat is None:
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

    # -----------------------------------------------------
    # CHECK NORMAL CYCLE
    # -----------------------------------------------------

    existing_task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if (
        existing_task
        and not existing_task.done()
    ):

        if update.message:

            await update.message.reply_text(
                "⚠️ A recurring session is already "
                "active in this group."
            )

        return

    # -----------------------------------------------------
    # START TEST
    # -----------------------------------------------------

    if update.message:

        await update.message.reply_text(
            "🧪 One-time test session starting..."
        )

    try:

        await run_session(
            chat_id,
            test_mode=True,
        )

        if update.message:

            await update.message.reply_text(
                "✅ One-time test completed.\n\n"
                "The 3-hour recurring cycle was not started."
            )

    except asyncio.CancelledError:

        raise

    except Exception as error:

        logger.exception(
            "One-time test failed: %s",
            error,
        )

        if update.message:

            await update.message.reply_text(
                "❌ Test failed. Check the server logs."
            )


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Show current session status."""

    chat = update.effective_chat

    if chat is None:
        return

    chat_id = chat.id

    task = GROUP_SESSION_TASKS.get(
        chat_id
    )

    if task and not task.done():

        status = (
            "🟢 ACTIVE\n\n"
            "The recurring session cycle is active.\n\n"
            "Sequence:\n"
            "Session → final CTA → 3-hour wait → "
            "next session."
        )

    else:

        status = (
            "🔴 INACTIVE\n\n"
            "No recurring session cycle is active.\n\n"
            "Use /start to begin."
        )

    if update.message:

        await update.message.reply_text(
            status
        )


async def add_group_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Save a group ID without starting a session.

    /start is still required to actually begin the cycle.
    """

    chat = update.effective_chat

    if chat is None:
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
            "✅ Group registered.\n\n"
            "Use /start when you want to begin the session cycle."
        )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Display available commands."""

    if update.message:

        await update.message.reply_text(
            "🤖 Two-Bot Promotional System\n\n"
            "/start — Start recurring sessions\n"
            "/stop — Stop recurring sessions\n"
            "/test — Run one test session\n"
            "/status — Show current status\n"
            "/addgroup — Register this group\n"
            "/help — Show this message"
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Log Telegram/application errors."""

    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )


# =========================================================
# CONFIGURE BOT
# =========================================================

def configure_application(
    application,
):
    """Register all command handlers."""

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

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_error_handler(
        error_handler
    )


# =========================================================
# MAIN (with conflict recovery)
# =========================================================

async def main():

    global APP_A
    global APP_B

    logger.info("========================================")
    logger.info("STARTING TWO-BOT SYSTEM")
    logger.info("========================================")

    # =====================================================
    # CREATE APPLICATIONS
    # =====================================================

    APP_A = Application.builder().token(TOKEN_A).build()
    APP_B = Application.builder().token(TOKEN_B).build()

    configure_application(APP_A)
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
    await APP_A.bot.delete_webhook(drop_pending_updates=True)

    logger.info("Removing Bot B webhook...")
    await APP_B.bot.delete_webhook(drop_pending_updates=True)

    # =====================================================
    # START APPLICATIONS
    # =====================================================

    await APP_A.start()
    await APP_B.start()

    logger.info("Both applications started.")

    # =====================================================
    # START POLLING WITH CONFLICT RECOVERY
    # =====================================================

    async def poll_bot(updater, name):
        """Poll a single bot with conflict recovery."""
        while True:
            try:
                await updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    timeout=60,
                )
                break  # Normal exit (shouldn't happen)
            except Exception as e:
                if "Conflict" in str(e):
                    logger.warning(f"{name}: Conflict detected, restarting in 10s...")
                    await asyncio.sleep(10)
                    continue
                else:
                    logger.error(f"{name}: {e}")
                    raise

    logger.info("Starting both bots polling concurrently...")

    try:
        await asyncio.gather(
            poll_bot(APP_A.updater, "Bot A"),
            poll_bot(APP_B.updater, "Bot B"),
        )
    except asyncio.CancelledError:
        logger.info("Polling cancelled.")

    # =====================================================
    # KEEP APPLICATION ALIVE (only if polling stops)
    # =====================================================

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Main application cancelled.")
    finally:
        logger.info("Beginning shutdown...")

        # =================================================
        # STOP GROUP TASKS
        # =================================================

        active_tasks = list(GROUP_SESSION_TASKS.values())
        logger.info("Stopping %s active group session(s).", len(active_tasks))

        for task in active_tasks:
            if not task.done():
                task.cancel()

        if active_tasks:
            await asyncio.gather(*active_tasks, return_exceptions=True)

        GROUP_SESSION_TASKS.clear()

        # =================================================
        # STOP POLLING
        # =================================================

        if APP_A and APP_A.updater and APP_A.updater.running:
            logger.info("Stopping Bot A polling...")
            await APP_A.updater.stop()

        if APP_B and APP_B.updater and APP_B.updater.running:
            logger.info("Stopping Bot B polling...")
            await APP_B.updater.stop()

        # =================================================
        # STOP APPLICATIONS
        # =================================================

        if APP_A:
            await APP_A.stop()

        if APP_B:
            await APP_B.stop()

        # =================================================
        # SHUTDOWN
        # =================================================

        if APP_A:
            await APP_A.shutdown()

        if APP_B:
            await APP_B.shutdown()

        logger.info("========================================")
        logger.info("TWO-BOT SYSTEM SHUTDOWN COMPLETE")
        logger.info("========================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as error:
        logger.exception("Fatal error: %s", error)
