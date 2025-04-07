import os
import logging
import asyncio
import nest_asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from db import Session, get_or_create_user, add_task, get_user_tasks, set_wallet
from models import User, UserTask, Task, Referral, task_instructions
from datetime import datetime

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_URL = os.getenv("BASE_URL")
if not TOKEN or not BASE_URL:
    raise ValueError("TOKEN or BASE_URL not set.")

ASK_WALLET = range(1)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Flask app
flask_app = Flask(__name__)

# Telegram bot application
telegram_app = ApplicationBuilder().token(TOKEN).get_updates_http_version("1.1").connection_pool_size(100).pool_timeout(10).build()

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# === Telegram Handlers ===
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start() called")
    session = Session()
    
    referral = context.args[0] if context.args else None
    user = get_or_create_user(session, update.effective_user.id, referral)
    add_task(session, user, Task.STARTED)

    msg = (
        "👋 Welcome to the best Crypto Bot ever! The Boss TEST is here! Let's get you started:\n\n"
    )
    for task, (desc, cmd) in task_instructions.items():
        if cmd:
            msg += f"➡️ *{desc}*: [{cmd}]({cmd})\n"
        else:
            msg += f"✅ *{desc}*\n"

    msg += "\n🌐 *Follow us on Social Media:*\n"
    msg += "🔗 [CoinMarketCap JBC Collective](https://coinmarketcap.com/community/profile/JimmyBossCollective/)\n"
    msg += "🔗 [CoinMarketCap JimmyBoss](https://coinmarketcap.com/community/profile/Jimmyboss/)\n"
    msg += "✖️ [X: JBC Collective](https://x.com/JBCcollective)\n"
    msg += "✖️ [X: Jimmy Boss](https://x.com/jimmyboss48)\n"
    msg += "📺 [YouTube Channel](https://www.youtube.com/channel/UCDEUuvfe5bkFgpSvi143uwQ)\n"

    if referral:
        msg += f"\n🎉 * You were referred by*: `{referral}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("status() called")
    session = Session()
    user = get_or_create_user(session, update.effective_user.id)
    add_task(session, user, Task.STATUS)
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
    print("complete_task() called")
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
    print("start_wallet_conversation() called")
    await update.message.reply_text("💼 Please send your wallet address now.")
    return ASK_WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("receive_wallet() called")
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
    print("cancel_wallet() called")
    await update.message.reply_text("❌ Wallet input cancelled.")
    return ConversationHandler.END

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("refer() called")
    session = Session()
    user = get_or_create_user(session, update.effective_user.id)

    # Ensure the bot's username is available
    bot_username = telegram_app.bot.username
    if not bot_username:
        await update.message.reply_text("❗ Unable to generate referral link. Bot username not found.")
        session.close()
        return

    # Generate a referral link using the bot's username
    referral_link = f"https://t.me/{bot_username}?start={user.id}"

    # Message to the user
    msg = (
        "🎉 *Invite your friends and earn rewards!*\n\n"
        "Share the referral link below with your friends:\n"
        f"🔗 [Click to Join]({referral_link})\n\n"
        "When your friends join using your referral link, you'll earn rewards!"
    )

    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()

async def dump_db_790(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("dump_db_790() called")
    session = Session()

    # Fetch all users
    users = session.query(User).all()
    user_data = "\n".join(
        [
            f"ID: {user.id}, Telegram ID: {user.telegram_id}, Wallet: {user.wallet_address}, "
            f"Referral Code: {user.referral_code}, Referred By: {user.referred_by}, "
            f"Referral Count: {user.referral_count}"
            for user in users
        ]
    )

    # Fetch all user tasks
    user_tasks = session.query(UserTask).all()
    task_data = "\n".join(
        [
            f"ID: {task.id}, User ID: {task.user_id}, Task: {task.task.value}, Completed At: {task.completed_at}"
            for task in user_tasks
        ]
    )

    # Fetch all referrals
    referrals = session.query(Referral).all()
    referral_data = "\n".join(
        [
            f"ID: {referral.id}, Referred By ID: {referral.referred_by_id}, "
            f"Referred User ID: {referral.referred_user_id}, Referred At: {referral.referred_at}"
            for referral in referrals
        ]
    )

    # Combine all data
    db_dump = (
        f"📋 *Users:*\n{user_data if user_data else 'No users found.'}\n\n"
        f"📋 *User Tasks:*\n{task_data if task_data else 'No tasks found.'}\n\n"
        f"📋 *Referrals:*\n{referral_data if referral_data else 'No referrals found.'}"
    )

    # Send the data as a message
    await update.message.reply_text(db_dump, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()

async def add_test_user_709(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("add_test_user_709() called")
    session = Session()

    # Check if the test user already exists
    telegram_id = "tonto001"
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        # Create the test user
        user = User(
            telegram_id=telegram_id,
            created_at=datetime.utcnow(),
            referral_code="TEST709"
        )
        session.add(user)
        session.commit()
        msg = "✅ Test user created successfully!"
    else:
        msg = "⚠️ Test user already exists!"

    # Generate the referral link
    referral_link = f"{BASE_URL}/start?ref={user.referral_code}"
    msg += f"\n\n🔗 *Referral Link*: [Click to Join]({referral_link})"

    # Send the message
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()

# Register Telegram handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("status", status))
telegram_app.add_handler(CommandHandler("complete_task", complete_task))
telegram_app.add_handler(CommandHandler("refer", refer))
telegram_app.add_handler(CommandHandler("dump_db_790", dump_db_790))
telegram_app.add_handler(CommandHandler("add_test_user_709", add_test_user_709))

wallet_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_wallet", start_wallet_conversation)],
    states={ASK_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wallet)]},
    fallbacks=[CommandHandler("cancel", cancel_wallet)],
)
telegram_app.add_handler(wallet_conv_handler)

# === Helper to Run Async Functions in Flask ===
def run_async(func):
    def wrapper(*args, **kwargs):
        print(f"run_async() called for {func.__name__}")
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper

# Webhook route
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
@run_async
async def webhook():
    print("webhook() called")
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return jsonify({"status": "ok"})

# Start Flask app
if __name__ == "__main__":
    print("Starting bot...")
    # Set up webhook and start Flask
    loop = asyncio.get_event_loop()
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.bot.set_webhook(WEBHOOK_URL))
    logging.info(f"✅ Webhook is set: {WEBHOOK_URL}")
    flask_app.run(host="0.0.0.0", port=5000)