"""
F1 Telegram Bot - FINAL FIXED VERSION
Solves webhook domain issues and initialization problems
"""

import os
import sys
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot, Message
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from f1_bot_live import (
    start,
    show_menu,
    button_handler,
    live_cmd,
    get_current_standings,
    get_constructor_standings,
    get_last_session_results,
    get_next_race,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_APP = None
WEBHOOK_SET = False  # CRITICAL: Prevents repeated webhook attempts
BOT_INITIALIZED = False  # Track if bot was ever initialized

# Track processed update IDs to prevent duplicate processing
PROCESSED_UPDATES = set()
MAX_PROCESSED_UPDATES = 1000  # Keep only recent updates to prevent memory issues

def is_update_processed(update_id):
    """Check if update has already been processed"""
    return update_id in PROCESSED_UPDATES

def mark_update_processed(update_id):
    """Mark update as processed"""
    PROCESSED_UPDATES.add(update_id)
    # Keep only recent updates to prevent memory issues
    if len(PROCESSED_UPDATES) > MAX_PROCESSED_UPDATES:
        # Remove oldest updates (this is a simple approach)
        PROCESSED_UPDATES.clear()

async def process_update_isolated(bot_app, update, update_id):
    """Process update in an isolated async context to prevent event loop conflicts"""
    try:
        # Ensure bot_app is provided
        if bot_app is None:
            logger.error(f"❌ Bot app is None for update {update_id}")
            return

        # Process the update (bot should already be initialized)
        await bot_app.process_update(update)
        logger.info(f"✅ Update {update_id} processed successfully")

    except Exception as e:
        logger.error(f"❌ Error in isolated update processing {update_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Handle specific errors
        error_str = str(e)
        if "Event loop is closed" in error_str:
            logger.warning("Event loop closed error - this should not happen with proper initialization")
        elif "not initialized" in error_str.lower():
            logger.warning("Application not initialized - this should not happen")

# Get webhook URL from environment variable
def get_webhook_url():
    """Get webhook URL from environment or use the default domain"""
    return os.getenv("WEBHOOK_URL", "https://f1bot2026update-rhidayetov9689-hrfji06h.leapcell.dev/webhook")

def get_bot_token():
    """Get bot token from environment or .env file"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            return token
    except ImportError:
        pass
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == "TELEGRAM_BOT_TOKEN" and not os.getenv(key):
                            return value
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    return None


async def setup_bot():
    """Initialize the Telegram bot application"""
    logger.info("=== BOT INITIALIZATION START ===")
    BOT_TOKEN = get_bot_token()
    logger.info(f"Bot token retrieved: {'YES' if BOT_TOKEN else 'NO'}")
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
        logger.error("Please set your Telegram bot token in the .env file or environment variables")
        logger.error("Get your bot token from @BotFather in Telegram")
        return None

    logger.info("Setting up Telegram bot application...")
    try:
        logger.info("Creating Application builder...")

        # Create HTTPXRequest with explicit client initialization
        import httpx
        from telegram.request import HTTPXRequest

        httpx_request = HTTPXRequest(
            connection_pool_size=20,
            read_timeout=30.0,
            write_timeout=30.0,
            connect_timeout=30.0,
            pool_timeout=30.0
        )

        # Ensure the client is initialized
        if not hasattr(httpx_request, '_client') or httpx_request._client is None:
            httpx_request._client = httpx.AsyncClient(
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                timeout=httpx.Timeout(30.0, read=30.0, write=30.0, pool=30.0),
            )

        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .request(httpx_request)
            .concurrent_updates(True)
            .build()
        )
        
        # Initialize the application properly
        await application.initialize()
        
        logger.info("Application created, adding handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", show_menu))
        # Create async wrapper functions for the command handlers
        async def standings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if isinstance(update.message, Message):
                await update.message.reply_text("⏳ Yüklənir...")
                message = get_current_standings()
                await update.message.reply_text(message, parse_mode="Markdown")

        async def constructors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if isinstance(update.message, Message):
                await update.message.reply_text("⏳ Yüklənir...")
                message = get_constructor_standings()
                await update.message.reply_text(message, parse_mode="Markdown")

        async def lastrace_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if isinstance(update.message, Message):
                await update.message.reply_text("⏳ Yüklənir...")
                message = get_last_session_results()
                await update.message.reply_text(message, parse_mode="Markdown")

        async def nextrace_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if isinstance(update.message, Message):
                await update.message.reply_text("⏳ Yüklənir...")
                message = get_next_race()
                await update.message.reply_text(message, parse_mode="Markdown")

        application.add_handler(CommandHandler("standings", standings_handler))
        application.add_handler(CommandHandler("constructors", constructors_handler))
        application.add_handler(CommandHandler("lastrace", lastrace_handler))
        application.add_handler(CommandHandler("nextrace", nextrace_handler))
        application.add_handler(CommandHandler("live", live_cmd))
        application.add_handler(CallbackQueryHandler(button_handler))

        logger.info("✅ Bot setup successful")
        logger.info("=== BOT INITIALIZATION COMPLETE ===")
        return application
    except Exception as e:
        logger.error(f"❌ Bot setup failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None

async def initialize_bot_app():
    """Initialize bot application and set webhook with flood control handling"""
    global BOT_APP, WEBHOOK_SET, BOT_INITIALIZED

    # Skip initialization if already done
    if BOT_INITIALIZED:
        logger.info("✅ Bot already initialized, reusing existing application")
        return True

    try:
        # Setup bot application (this already calls initialize())
        bot_app = await setup_bot()
        if not bot_app:
            logger.error("❌ Bot setup failed - no bot application")
            return False

        # Don't call initialize() again - setup_bot() already did this
        BOT_APP = bot_app
        BOT_INITIALIZED = True
        logger.info("✅ Bot application initialized successfully")

        # Set webhook if not already set
        webhook_url = get_webhook_url()
        bot = bot_app.bot

        try:
            webhook_info = await bot.get_webhook_info()
            current_url = webhook_info.url

            if current_url and current_url == webhook_url:
                logger.info(f"✅ Webhook already set to correct URL: {webhook_url}")
                WEBHOOK_SET = True
                return True
            elif current_url:
                logger.info(f"🔄 Webhook exists but wrong URL. Current: {current_url}, Needed: {webhook_url}")
            else:
                logger.info("🆕 No webhook set, will set new one")

        except Exception as e:
            if "webhook is not set" in str(e).lower():
                logger.info("🆕 No existing webhook found")
            else:
                logger.warning(f"⚠️ Could not check webhook status: {e}")

        # Set webhook
        try:
            logger.info(f"🔧 Setting webhook to: {webhook_url}")
            result = await bot.set_webhook(url=webhook_url)

            if result:
                WEBHOOK_SET = True
                logger.info(f"✅ Webhook successfully set to: {webhook_url}")
                return True
            else:
                logger.error("❌ Webhook set returned False")
                return False

        except Exception as e:
            error_str = str(e)
            if "Retry after" in error_str or "Flood control" in error_str:
                logger.warning(f"⚠️ Telegram flood control activated! {e}")
                logger.warning("⏳ Waiting before retry...")
                await asyncio.sleep(10)
                return await initialize_bot_app()
            else:
                logger.error(f"❌ Failed to set webhook: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return False

    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


@app.route("/")
def home():
    return {
        "status": "F1 Telegram Bot is running!",
        "version": "1.2.0",
        "fix": "webhook_domain_issue_fixed",
        "deployment": "Leapcell",
        "webhook_url": get_webhook_url(),
    }

@app.route("/health")
def health_check():
    return {
        "status": "healthy",
        "initialized": BOT_APP is not None,
        "webhook_url": get_webhook_url(),
    }

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming webhook updates from Telegram"""
    global BOT_APP
    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        logger.warning("Invalid JSON received")
        return jsonify({"status": "ok"}), 200

    update_id = json_data.get("update_id", "unknown")
    logger.info(f"📥 Update {update_id} received")

    # Check for duplicate updates to prevent multiple processing
    if is_update_processed(update_id):
        logger.info(f"⚠️ Duplicate update {update_id} detected, skipping")
        return jsonify({"status": "ok"}), 200

    # Mark update as being processed
    mark_update_processed(update_id)

    try:
        # Initialize bot application if not already done
        if BOT_APP is None:
            logger.info("Initializing bot application...")
            success = await initialize_bot_app()
            if not success:
                logger.error("❌ Failed to initialize bot")
                return jsonify({"status": "error", "message": "Bot initialization failed"}), 500

        bot_app = BOT_APP
        if bot_app is None or not hasattr(bot_app, "bot") or bot_app.bot is None:
            logger.error("Bot app or bot is None")
            return jsonify({"status": "ok"}), 200

        bot = bot_app.bot
        update = Update.de_json(json_data, bot)
        if update is None:
            logger.warning("Failed to create update object")
            return jsonify({"status": "ok"}), 200

        # Process update directly in the same async context
        await process_update_isolated(bot_app, update, update_id)

    except Exception as e:
        logger.error(f"❌ Error processing update {update_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

    # Return success response
    return jsonify({"status": "ok"}), 200


@app.route("/debug")
def debug():
    """Debug endpoint to check bot status"""
    token = get_bot_token()
    import_status = {}
    
    try:
        from f1_bot_live import start, get_current_standings
        import_status["f1_bot_live"] = "OK"
    except Exception as e:
        import_status["f1_bot_live"] = f"ERROR: {e}"

    try:
        import telegram
        import_status["telegram"] = f"OK (v{telegram.__version__})"
    except Exception as e:
        import_status["telegram"] = f"ERROR: {e}"

    return jsonify({
        "bot_token_set": bool(token),
        "bot_initialized": BOT_APP is not None,
        "version": "1.2.0",
        "imports": import_status,
        "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
        "webhook_url": get_webhook_url(),
        "environment": {
            "webhook_url_env": os.getenv("WEBHOOK_URL", "NOT_SET"),
            "telegram_bot_token_env": "SET" if os.getenv("TELEGRAM_BOT_TOKEN") else "NOT_SET",
        }
    })

@app.route("/webhook-info")
def webhook_info():
    """Endpoint to check webhook status"""
    webhook_url = get_webhook_url()
    return jsonify({
        "webhook_url": webhook_url,
        "bot_initialized": BOT_APP is not None,
    })

@app.route("/set-webhook", methods=["POST"])
def manual_set_webhook():
    """Endpoint to manually set the webhook"""
    global BOT_APP
    if BOT_APP is None:
        return jsonify({"status": "error", "message": "Bot not initialized"}), 500
    
    try:
        webhook_url = get_webhook_url()
        logger.info(f"Manually setting webhook to: {webhook_url}")
        success = asyncio.run(set_webhook_manually(webhook_url))
        if success:
            logger.info("✅ Webhook set successfully")
            return jsonify({"status": "success", "webhook_url": webhook_url}), 200
        else:
            logger.warning("⚠️ Failed to set webhook")
            return jsonify({"status": "error", "message": "Failed to set webhook"}), 500
    except Exception as e:
        logger.error(f"❌ Failed to set webhook manually: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

async def set_webhook_manually(webhook_url):
    """Manually set webhook URL"""
    global BOT_APP
    if BOT_APP is None:
        logger.warning("Bot not initialized, cannot set webhook")
        return False

    try:
        bot = BOT_APP.bot
        logger.info(f"Setting webhook to: {webhook_url}")
        result = await bot.set_webhook(url=webhook_url)
        if result:
            logger.info(f"✅ Webhook set to: {webhook_url}")
            # Verify webhook is set
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info}")
        else:
            logger.warning("⚠️ Webhook set returned False")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

# Removed unused process_update_async function

def main():
    """Main initialization function - only run in development"""
    logger.info("🚀 Starting F1 Telegram Bot initialization...")

    # Only initialize on startup if not in production/serverless environment
    # In serverless environments, initialization should happen on first webhook request
    if os.getenv("FLASK_ENV") == "development" or not os.getenv("WEBHOOK_URL"):
        try:
            success = asyncio.run(initialize_bot_app())
            if success:
                logger.info("✅ Bot initialized successfully on startup!")
            else:
                logger.warning("⚠️ Bot initialization failed on startup - will try on first request")
        except Exception as e:
            logger.error(f"❌ Startup initialization error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    else:
        logger.info("🏭 Serverless environment detected - skipping startup initialization")

# Initialize bot when Flask app starts (for Gunicorn compatibility)
def init_app():
    # Only initialize if we're in development or if explicitly requested
    # In production serverless, let webhook requests handle initialization
    if os.getenv("FLASK_ENV") == "development" or os.getenv("FORCE_INIT", "").lower() == "true":
        with app.app_context():
            main()
    else:
        logger.info("🏭 Production serverless mode - initialization deferred to first webhook request")

# Call init_app when this module is imported - but only in appropriate environments
init_app()

if __name__ == "__main__":
    logger.info("🌐 Flask server starting...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False, threaded=True)
