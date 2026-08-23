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

# Example:
#
# {
#     -100123456789: asyncio.Task(...)
# }
#
GROUP_SESSION_TASKS = {}


# =========================================================
# NEUTRAL TEST CONVERSATION
# =========================================================
#
# These are deliberately neutral test messages.
# They do not simulate customers, testimonials,
# endorsements, financial claims, or promotional activity.
# =========================================================

CONVERSATION_PAIRS = [
    (
        "🤖 Bot A: Hello! This is a system test message.",
        "🤖 Bot B: Bot B received the message successfully.",
    ),
    (
        "📋 Bot A: Checking the message sequence now.",
        "📋 Bot B: Sequence check completed successfully.",
    ),
    (
        "🔄 Bot A: Testing communication between the two bots.",
        "🔄 Bot B: Communication test received.",
    ),
    (
        "⏱️ Bot A: Testing the scheduled delay.",
        "⏱️ Bot B: Scheduled delay test completed.",
    ),
    (
        "📡 Bot A: Testing message delivery to this group.",
        "📡 Bot B: Message delivery is working.",
    ),
    (
        "🧪 Bot A: Running another neutral system check.",
        "🧪 Bot B: Neutral system check received.",
    ),
    (
        "✅ Bot A: The first part of this test is complete.",
        "✅ Bot B: The second part of this test is complete.",
    ),
    (
        "🔔 Bot A: This is a normal automated test notification.",
        "🔔 Bot B: Notification received successfully.",
    ),
]


# =========================================================
# FINAL SESSION MESSAGES
# =========================================================

FINAL_CALL_A = (
    "🏁 Bot A: Test session is reaching its final step.\n\n"
    "The session will finish after this message."
)

FINAL_CALL_B = (
    "✅ Bot B: Test session completed successfully.\n\n"
    "The 3-hour countdown will now begin."
)


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
    # SELECT MESSAGES
    # -----------------------------------------------------

    if test_mode:

        number_of_pairs = min(
            3,
            len(CONVERSATION_PAIRS),
        )

        wait_min = TEST_WAIT_MIN
        wait_max = TEST_WAIT_MAX

    else:

        number_of_pairs = min(
            6,
            len(CONVERSATION_PAIRS),
        )

        wait_min = NORMAL_WAIT_MIN
        wait_max = NORMAL_WAIT_MAX

    pairs = random.sample(
        CONVERSATION_PAIRS,
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

    await send_bot_a(
        chat_id,
        FINAL_CALL_A,
    )

    await asyncio.sleep(3)

    await send_bot_b(
        chat_id,
        FINAL_CALL_B,
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
        Session 1
           ↓
        Final CTA/message
           ↓
        3-hour wait
           ↓
        Session 2
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
            # NEXT SESSION
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
# /START
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
                "The first test session will begin now.\n"
                "The 3-hour countdown starts only after "
                "the session completely finishes."
            )

    else:

        if update.message:

            await update.message.reply_text(
                "ℹ️ A session cycle is already active "
                "in this group."
            )


# =========================================================
# /STOP
# =========================================================

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


# =========================================================
# /TEST
# =========================================================

async def test_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Run one neutral test session.

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


# =========================================================
# /STATUS
# =========================================================

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
            "Session → final message → 3-hour wait → "
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


# =========================================================
# /ADDGROUP
# =========================================================

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


# =========================================================
# /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Display available commands."""

    if update.message:

        await update.message.reply_text(
            "🤖 Two-Bot Test System\n\n"
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
# MAIN
# =========================================================

async def main():
    """
    Run both Telegram bots on the SAME asyncio event loop.

    This avoids:
      - threading
      - separate asyncio loops
      - cross-loop locks
      - set_signal_handlers()
      - run_polling() conflicts
    """

    global APP_A
    global APP_B

    logger.info(
        "========================================"
    )

    logger.info(
        "STARTING TWO-BOT SYSTEM"
    )

    logger.info(
        "========================================"
    )

    # =====================================================
    # CREATE APPLICATIONS
    # =====================================================

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

    configure_application(
        APP_A
    )

    configure_application(
        APP_B
    )

    # =====================================================
    # INITIALIZE
    # =====================================================

    logger.info(
        "Initializing Bot A..."
    )

    await APP_A.initialize()

    logger.info(
        "Initializing Bot B..."
    )

    await APP_B.initialize()

    # =====================================================
    # REMOVE WEBHOOKS
    # =====================================================

    logger.info(
        "Removing Bot A webhook..."
    )

    await APP_A.bot.delete_webhook(
        drop_pending_updates=True
    )

    logger.info(
        "Removing Bot B webhook..."
    )

    await APP_B.bot.delete_webhook(
        drop_pending_updates=True
    )

    # =====================================================
    # START APPLICATIONS
    # =====================================================

    logger.info(
        "Starting Bot A..."
    )

    await APP_A.start()

    logger.info(
        "Starting Bot B..."
    )

    await APP_B.start()

    # =====================================================
    # START POLLING
    # =====================================================

    logger.info(
        "Starting Bot A polling..."
    )

    await APP_A.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    logger.info(
        "Starting Bot B polling..."
    )

    await APP_B.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    logger.info(
        "========================================"
    )

    logger.info(
        "BOTH BOTS ARE ONLINE"
    )

    logger.info(
        "No session will start automatically."
    )

    logger.info(
        "Use /start inside a group."
    )

    logger.info(
        "========================================"
    )

    # =====================================================
    # KEEP APPLICATION ALIVE
    # =====================================================

    try:

        await asyncio.Event().wait()

    except asyncio.CancelledError:

        logger.info(
            "Main application cancelled."
        )

    finally:

        logger.info(
            "Beginning shutdown..."
        )

        # =================================================
        # STOP GROUP TASKS
        # =================================================

        active_tasks = list(
            GROUP_SESSION_TASKS.values()
        )

        logger.info(
            "Stopping %s active group session(s).",
            len(active_tasks),
        )

        for task in active_tasks:

            if not task.done():

                task.cancel()

        if active_tasks:

            await asyncio.gather(
                *active_tasks,
                return_exceptions=True,
            )

        GROUP_SESSION_TASKS.clear()

        # =================================================
        # STOP POLLING
        # =================================================

        if (
            APP_A
            and APP_A.updater
            and APP_A.updater.running
        ):

            logger.info(
                "Stopping Bot A polling..."
            )

            await APP_A.updater.stop()

        if (
            APP_B
            and APP_B.updater
            and APP_B.updater.running
        ):

            logger.info(
                "Stopping Bot B polling..."
            )

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

        logger.info(
            "========================================"
        )

        logger.info(
            "TWO-BOT SYSTEM SHUTDOWN COMPLETE"
        )

        logger.info(
            "========================================"
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
            "Fatal error: %s",
            error,
        )
