import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)

from dotenv import load_dotenv
from db import Session, get_or_create_user, add_task, get_user_tasks, set_wallet
from models import Task, task_instructions
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_URL = os.getenv("BASE_URL")
if not TOKEN or not BASE_URL:
    raise ValueError("TOKEN or BASE_URL not set.")

ASK_WALLET = range(1)

# === Flask and Telegram App
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# === Telegram Handlers (same as before)
# ... your handlers like start, status, add_wallet, etc ...

# Register handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("status", status))
telegram_app.add_handler(CommandHandler("complete_task", complete_task))

wallet_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_wallet", start_wallet_conversation)],
    states={ASK_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wallet)]},
    fallbacks=[CommandHandler("cancel", cancel_wallet)],
)
telegram_app.add_handler(wallet_conv_handler)

# === Webhook route
@flask_app.post(WEBHOOK_PATH)
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

# === Start Flask + Set Webhook
if __name__ == "__main__":
    import asyncio

    async def startup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        flask_app.run(host="0.0.0.0", port=5000)

    asyncio.run(startup())
