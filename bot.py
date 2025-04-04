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

# === Telegram handlers ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.effective_user.id)
    add_task(session, user, Task.STARTED)

    msg = "👋 Welcome to the best Crypto Bot ever! The Boss TEST is here!  Let's get you started:\n\n"
    for task, (desc, cmd) in task_instructions.items():
        if cmd:
            msg += f"➡️ *{desc}*: [{cmd}]({cmd})\n"
        else:
            msg += f"✅ *{desc}*\n"
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.effective_user.id)
    completed = set(get_user_tasks(session, user))

    msg = "📋 *Your task progress:*\n\n"
    for task, (desc, cmd) in task_instructions.items():
        if task in completed:
            msg += f"✅ *{desc}* — done\n"
        elif cmd:
            msg += f"❌ *{desc}*: [{cmd}]({cmd})\n"
        else:
            msg += f"❌ *{desc}*\n"

    if user.wallet_address:
        msg += f"\n💳 *Wallet Address*: `{user.wallet_address}`"
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Usage: /complete_task WALLET_ADDED")
        return
    try:
        task_name = context.args[0]
        task_enum = Task[task_name]
    except KeyError:
        await update.message.reply_text("❗ Invalid task. Try: STARTED, WALLET_ADDED, REFERRAL_DONE, COMPLETED.")
        return

    session = Session()
    user = get_or_create_user(session, update.effective_user.id)
    add_task(session, user, task_enum)
    await update.message.reply_text(f"✅ Task '{task_enum.value}' marked complete.")
    session.close()

async def start_wallet_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💼 Please send your wallet address now.")
    return ASK_WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = update.message.text.strip()
    if len(wallet_address) < 10:
        await update.message.reply_text("❗ Invalid wallet address. Please try again.")
        return ASK_WALLET

    session = Session()
    user = get_or_create_user(session, update.effective_user.id)
    if set_wallet(session, user, wallet_address):
        add_task(session, user, Task.WALLET_ADDED)
        await update.message.reply_text(f"✅ Wallet saved: `{wallet_address}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Could not save your wallet. Please try again.")
    session.close()
    return ConversationHandler.END

async def cancel_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Wallet input cancelled.")
    return ConversationHandler.END


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

    async def start_bot():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        print("✅ Webhook set:", WEBHOOK_URL)

    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    flask_app.run(host="0.0.0.0", port=5000)


