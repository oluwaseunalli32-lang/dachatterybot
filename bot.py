import asyncio
import logging
import os
import random

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler


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

GROUP_IDS_FILE = "group_ids.txt"

APP_A = None
APP_B = None


# =========================================================
# CONVERSATION PAIRS
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
        "That's a nice bonus on top of the competitive rate.",
    ),
    (
        "🔥 400 USDT+ gives you ₹400 – that's a 1% reward!",
        "And it scales up – 1000 USDT gives ₹1,200.",
    ),
    (
        "💎 Exchange 2000 USDT and get ₹3,000 reward!",
        "Yes, and at 4000 USDT it's ₹8,000.",
    ),
    (
        "🏅 The top tier: 6000 USDT+ unlocks ₹15,000 bonus!",
        "That's the highest reward tier available.",
    ),
    (
        "🔔 The official registration link is available.",
        "The registration process is simple and quick.",
    ),
    (
        "🤝 Invite your friends and build your team.",
        "Active referrals can help grow the community.",
    ),
    (
        "📩 For more details, contact @jetlee261.",
        "They can provide additional information.",
    ),
    (
        "🚀 USDT is widely used for digital transactions.",
        "The exchange offer includes additional reward tiers.",
    ),
    (
        "⏰ The current offer is available for a limited period.",
        "It's worth checking the available reward conditions.",
    ),
    (
        "📈 The current USDT exchange rate is 108.5.",
        "Always verify the current rate before making a transaction.",
    ),
    (
        "🎯 Higher exchange amounts unlock higher reward tiers.",
        "The reward structure increases based on volume.",
    ),
    (
        "💬 The community continues to grow.",
        "You can contact support for additional information.",
    ),
    (
        "🔄 Exchange more, unlock higher reward levels.",
        "The rewards are based on the applicable exchange tier.",
    ),
]


# =========================================================
# FINAL MESSAGES
# =========================================================

FINAL_CALL_A = (
    "USDT EXCHANGE REWARDS ARE LIVE! 🔄\n\n"
    "🏆 USDT Rate: 108.5\n\n"
    "📌 OFFICIAL LINK:\n\n"
    "https://wallet.paisa-base.com/register?inviteCode=phar6p\n\n"
    "🔔 Exchange More, Earn More!\n\n"
    "☄️ Reward tiers:\n"
    "⭐️ 100 USDT+ → ₹80 Reward\n"
    "⭐️ 400 USDT+ → ₹400 Reward\n"
    "⭐️ 1000 USDT+ → ₹1,200 Reward\n"
    "⭐️ 2000 USDT+ → ₹3,000 Reward\n"
    "⭐️ 4000 USDT+ → ₹8,000 Reward\n"
    "🏆 6000 USDT+ → ₹15,000 Reward\n\n"
    "📩 DM @jetlee261 for details!"
)

FINAL_CALL_B = (
    "💬 Contact @jetlee261 for more information.\n\n"
    "Check the current terms before participating. 🚀"
)


# =========================================================
# GROUP ID STORAGE
# =========================================================

def load_group_ids():
    """Load all saved group IDs."""

    try:
        group_ids = []

        with open(
            GROUP_IDS_FILE,
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
                        f"Ignoring invalid group ID: {line}"
                    )

        return group_ids

    except FileNotFoundError:
        return []


def save_group_id(chat_id):
    """Save a group ID if it is not already saved."""

    group_ids = load_group_ids()

    if chat_id not in group_ids:

        group_ids.append(chat_id)

        with open(
            GROUP_IDS_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            for group_id in group_ids:
                file.write(f"{group_id}\n")

        logger.info(
            f"Saved group ID: {chat_id}"
        )


# =========================================================
# SEND MESSAGES
# =========================================================

async def send_to_groups(
    text_a=None,
    text_b=None,
):
    """Send messages from Bot A and/or Bot B."""

    if APP_A is None or APP_B is None:
        logger.error(
            "Bots are not ready yet."
        )
        return

    group_ids = load_group_ids()

    if not group_ids:
        logger.warning(
            "No groups have been registered."
        )
        return

    for chat_id in group_ids:

        if text_a:

            try:
                await APP_A.bot.send_message(
                    chat_id=chat_id,
                    text=text_a,
                )

                logger.info(
                    f"Bot A sent message to {chat_id}"
                )

            except Exception as error:

                logger.error(
                    f"Bot A failed to send to "
                    f"{chat_id}: {error}"
                )

        if text_b:

            try:
                await APP_B.bot.send_message(
                    chat_id=chat_id,
                    text=text_b,
                )

                logger.info(
                    f"Bot B sent message to {chat_id}"
                )

            except Exception as error:

                logger.error(
                    f"Bot B failed to send to "
                    f"{chat_id}: {error}"
                )


# =========================================================
# CHAT SESSION
# =========================================================

async def daily_session(test_mode=False):

    logger.info(
        "========================================"
    )

    logger.info(
        "CHAT SESSION STARTED"
    )

    logger.info(
        "========================================"
    )

    if test_mode:

        min_wait = 5
        max_wait = 10

        pairs = random.sample(
            CONVERSATION_PAIRS,
            min(
                3,
                len(CONVERSATION_PAIRS),
            ),
        )

    else:

        # Normal chat timing
        min_wait = 60
        max_wait = 180

        # Select up to 15 conversations
        pairs = random.sample(
            CONVERSATION_PAIRS,
            min(
                15,
                len(CONVERSATION_PAIRS),
            ),
        )

    for index, (
        message_a,
        message_b,
    ) in enumerate(pairs):

        # -------------------------------------
        # BOT A SENDS
        # -------------------------------------

        await send_to_groups(
            text_a=message_a,
        )

        wait_time = random.randint(
            min_wait,
            max_wait,
        )

        logger.info(
            f"Bot A sent message. "
            f"Waiting {wait_time} seconds."
        )

        await asyncio.sleep(
            wait_time
        )

        # -------------------------------------
        # BOT B REPLIES
        # -------------------------------------

        await send_to_groups(
            text_b=message_b,
        )

        # -------------------------------------
        # WAIT BEFORE NEXT PAIR
        # -------------------------------------

        if index < len(pairs) - 1:

            wait_time = random.randint(
                min_wait,
                max_wait,
            )

            logger.info(
                f"Bot B replied. "
                f"Waiting {wait_time} seconds."
            )

            await asyncio.sleep(
                wait_time
            )

    # -----------------------------------------
    # FINAL MESSAGES
    # -----------------------------------------

    await asyncio.sleep(5)

    await send_to_groups(
        text_a=FINAL_CALL_A,
    )

    await asyncio.sleep(3)

    await send_to_groups(
        text_b=FINAL_CALL_B,
    )

    logger.info(
        "========================================"
    )

    logger.info(
        "CHAT SESSION COMPLETED"
    )

    logger.info(
        "========================================"
    )


# =========================================================
# BOT HANDLERS
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message:

        await update.message.reply_text(
            "🤖 Bot is active!\n\n"
            "Use /addgroup to register this group.\n"
            "Use /test to start a test session."
        )


async def add_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type in (
        "group",
        "supergroup",
    ):

        save_group_id(
            chat.id
        )

        if update.message:

            await update.message.reply_text(
                "✅ This group has been registered."
            )

    else:

        if update.message:

            await update.message.reply_text(
                "❌ Please run this command inside a group."
            )


async def new_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type in (
        "group",
        "supergroup",
    ):

        save_group_id(
            chat.id
        )

        try:

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "🎉 Thanks for adding the bot!\n\n"
                    "This group has been registered."
                ),
            )

        except Exception as error:

            logger.error(
                f"Could not send welcome message: {error}"
            )


async def test_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if APP_A is None or APP_B is None:

        if update.message:

            await update.message.reply_text(
                "⚠️ Bots are still starting."
            )

        return

    chat = update.effective_chat

    if not chat:
        return

    chat_id = chat.id

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🧪 Test session started!"
        ),
    )

    pairs = random.sample(
        CONVERSATION_PAIRS,
        min(
            3,
            len(CONVERSATION_PAIRS),
        ),
    )

    for message_a, message_b in pairs:

        await APP_A.bot.send_message(
            chat_id=chat_id,
            text=message_a,
        )

        await asyncio.sleep(5)

        await APP_B.bot.send_message(
            chat_id=chat_id,
            text=message_b,
        )

        await asyncio.sleep(5)

    await APP_A.bot.send_message(
        chat_id=chat_id,
        text=FINAL_CALL_A,
    )

    await asyncio.sleep(3)

    await APP_B.bot.send_message(
        chat_id=chat_id,
        text=FINAL_CALL_B,
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Test complete!",
    )


# =========================================================
# MAIN APPLICATION (FIXED)
# =========================================================

async def main():

    global APP_A
    global APP_B

    logger.info(
        "========================================"
    )

    logger.info(
        "STARTING BOT A AND BOT B"
    )

    logger.info(
        "========================================"
    )

    # -----------------------------------------
    # CREATE APPLICATIONS
    # -----------------------------------------

    APP_A = (
        Application.builder()
        .token(TOKEN_A)
        .build()
    )

    APP_B = (
        Application.builder()
        .token(TOKEN_B)
        .build()
    )

    # -----------------------------------------
    # BOT A HANDLERS
    # -----------------------------------------

    APP_A.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    APP_A.add_handler(
        CommandHandler(
            "addgroup",
            add_group,
        )
    )

    APP_A.add_handler(
        CommandHandler(
            "test",
            test_handler,
        )
    )

    APP_A.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            new_group,
        )
    )

    # -----------------------------------------
    # BOT B HANDLERS
    # -----------------------------------------

    APP_B.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    APP_B.add_handler(
        CommandHandler(
            "addgroup",
            add_group,
        )
    )

    APP_B.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            new_group,
        )
    )

    # -----------------------------------------
    # INITIALIZE BOTH BOTS
    # -----------------------------------------

    logger.info(
        "Initializing Bot A..."
    )

    await APP_A.initialize()

    logger.info(
        "Initializing Bot B..."
    )

    await APP_B.initialize()

    # -----------------------------------------
    # CLEAR WEBHOOKS
    # -----------------------------------------

    await APP_A.bot.delete_webhook(
        drop_pending_updates=True
    )

    await APP_B.bot.delete_webhook(
        drop_pending_updates=True
    )

    # -----------------------------------------
    # START APPLICATIONS
    # -----------------------------------------

    await APP_A.start()

    await APP_B.start()

    logger.info(
        "Applications started."
    )

    # =====================================================
    # SCHEDULER – Start it BEFORE polling
    # =====================================================

    scheduler = AsyncIOScheduler(
        timezone="UTC"
    )

    scheduler.add_job(
        daily_session,
        trigger="interval",
        hours=3,
        id="chat_session",
        replace_existing=True,
        max_instances=1,          # Prevent overlapping sessions
        coalesce=True,            # Combine missed runs
        kwargs={
            "test_mode": False,
        },
    )

    scheduler.start()

    logger.info(
        "Scheduler started. Chat session will run every 3 hours."
    )

    # -----------------------------------------
    # Start first session immediately
    # -----------------------------------------

    asyncio.create_task(
        daily_session(
            test_mode=False
        )
    )

    logger.info(
        "First chat session started immediately."
    )

    # =====================================================
    # START POLLING FOR BOTH BOTS CONCURRENTLY
    # =====================================================

    logger.info(
        "Starting polling for both bots..."
    )

    try:

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

    except asyncio.CancelledError:

        logger.info(
            "Application shutdown requested."
        )

    finally:

        logger.info(
            "Shutting down..."
        )

        # Stop scheduler
        scheduler.shutdown(
            wait=False
        )

        # Stop polling
        await APP_A.updater.stop()

        await APP_B.updater.stop()

        # Stop applications
        await APP_A.stop()

        await APP_B.stop()

        # Shutdown applications
        await APP_A.shutdown()

        await APP_B.shutdown()

        logger.info(
            "Shutdown complete."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped manually."
        )

    except Exception as error:

        logger.exception(
            f"Fatal error: {error}"
        )
