"""
F1 Telegram Bot - Vercel Version
Main Flask application for Vercel deployment
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import bot functionality
from f1_bot import (
    start,
    show_menu,
    button_handler,
    standings_cmd,
    constructors_cmd,
    lastrace_cmd,
    nextrace_cmd,
    live_cmd,
    streams_cmd,
    addstream_cmd,
    removestream_cmd,
    streamhelp_cmd,
    playstream_cmd,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global reference for bot application
BOT_APP = None


def setup_bot():
    """Setup and return the Telegram bot application"""
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except ImportError:
        # Fallback: manually read .env file if python-dotenv is not installed
        if not os.getenv("TELEGRAM_BOT_TOKEN") and os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if not os.getenv(key):
                                os.environ[key] = value
            except Exception:
                pass

    # Get bot token from environment variable
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        logger.error("Get your token from @BotFather: https://t.me/BotFather")
        return None

    # Create application with proper configuration for v20.7
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("standings", standings_cmd))
    application.add_handler(CommandHandler("constructors", constructors_cmd))
    application.add_handler(CommandHandler("lastrace", lastrace_cmd))
    application.add_handler(CommandHandler("nextrace", nextrace_cmd))
    application.add_handler(CommandHandler("live", live_cmd))
    application.add_handler(CommandHandler("streams", streams_cmd))
    application.add_handler(CommandHandler("addstream", addstream_cmd))
    application.add_handler(CommandHandler("removestream", removestream_cmd))
    application.add_handler(CommandHandler("playstream", playstream_cmd))
    application.add_handler(CommandHandler("streamhelp", streamhelp_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))

    return application


@app.route("/")
def home():
    """Health check endpoint for Vercel"""
    return {
        "status": "F1 Telegram Bot is running!",
        "version": "1.0.0",
        "timestamp": "2025-12-29T08:26:00Z",
        "deployment": "Vercel",
    }


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "F1 Telegram Bot", "deployment": "Vercel"}


@app.route("/webhook", methods=["POST"])
async def webhook():
    """Telegram webhook endpoint"""
    global BOT_APP

    if BOT_APP is None:
        BOT_APP = setup_bot()
        if BOT_APP is None:
            return jsonify({"error": "Bot not configured"}), 500

    try:
        update = Update.de_json(request.get_json(force=True), BOT_APP.bot)
        await BOT_APP.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Local development mode
    BOT_APP = setup_bot()
    if BOT_APP:
        logger.info("Starting F1 Bot in local mode...")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    else:
        logger.error("Failed to start bot")
        sys.exit(1)
