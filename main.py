import os
import logging
import sys

# Ensure logging is configured BEFORE anything else imports f1_bot_live
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Now import handlers
try:
    from f1_bot_live import (
        start, 
        show_menu, 
        button_handler, 
        live_cmd, 
        standings_cmd, 
        constructors_cmd, 
        lastrace_cmd, 
        nextrace_cmd
    )
except ImportError as e:
    logger.error(f"Failed to import handlers: {e}")
    sys.exit(1)

from telegram.ext import Application, CommandHandler, CallbackQueryHandler

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)
    
    # Force the root logger to INFO in case f1_bot_live changed it
    logging.getLogger().setLevel(logging.INFO)
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("standings", standings_cmd))
    application.add_handler(CommandHandler("constructors", constructors_cmd))
    application.add_handler(CommandHandler("lastrace", lastrace_cmd))
    application.add_handler(CommandHandler("nextrace", nextrace_cmd))
    application.add_handler(CommandHandler("live", live_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting in POLLING mode (24/7 stable execution)...")
    application.run_polling()

if __name__ == "__main__":
    main()
