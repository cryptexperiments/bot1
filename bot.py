import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler, filters

from db import Session, get_or_create_user, add_task, get_user_tasks, set_wallet
from models import Task, task_instructions
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() 
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("No TOKEN found in environment variables.")

ASK_WALLET = range(1)

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

    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    session.close()


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

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Please provide your wallet address.\nUsage: /add_wallet <your_wallet>")
        return

    wallet_address = context.args[0]

    # You can add a proper blockchain-specific validation here
    if len(wallet_address) < 10:
        await update.message.reply_text("❗ Invalid wallet address.")
        return

    session = Session()
    user = get_or_create_user(session, update.effective_user.id)

    if set_wallet(session, user, wallet_address):
        add_task(session, user, Task.WALLET_ADDED)
        await update.message.reply_text(f"✅ Wallet saved: `{wallet_address}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Something went wrong saving your wallet.")
    session.close()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def start_wallet_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💼 Please send your wallet address now.")
    return ASK_WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = update.message.text.strip()

    # Simple length check — replace with proper validation if needed
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



app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("complete_task", complete_task))
app.add_handler(CommandHandler("status", status))

wallet_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_wallet", start_wallet_conversation)],
    states={
        ASK_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wallet)]
    },
    fallbacks=[CommandHandler("cancel", cancel_wallet)],
)

app.add_handler(wallet_conv_handler)


if __name__ == "__main__":
    print("🤖 Bot is running...")
    app.run_polling()
