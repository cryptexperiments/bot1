import pytest
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot import telegram_app

# --- Definición de DummyBot para capturar mensajes enviados ---
class DummyBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))
        return

# --- Fixture que reemplaza el bot real con uno dummy ---
@pytest.fixture
def dummy_bot(monkeypatch):
    dbot = DummyBot()
    monkeypatch.setattr(telegram_app, "bot", dbot)
    return dbot

# --- Fixture para inicializar la aplicación ---
@pytest.fixture(scope="function", autouse=True)
async def initialize_app():
    telegram_app.bot = dummy_bot
    await telegram_app.initialize()
    yield
    await telegram_app.shutdown()

# --- Función auxiliar para crear un objeto Update simulado ---
def create_update(command_text, chat_id=123456, user_id=111):
    update_dict = {
        "update_id": 1000001,
        "message": {
            "message_id": 1,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": chat_id,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1610000000,
            "text": command_text
        }
    }
    return Update.de_json(update_dict, bot=telegram_app.bot)

# --- Tests ---
@pytest.mark.asyncio
async def test_start_command(dummy_bot):
    update = create_update("/start")
    context = ContextTypes.DEFAULT_TYPE.from_update(update, telegram_app)
    await telegram_app.process_update(update)
    messages = dummy_bot.sent_messages
    assert any("Welcome" in text or "best Crypto Bot" in text for (_, text) in messages), \
        "El mensaje de bienvenida no se envió"

@pytest.mark.asyncio
async def test_status_command(dummy_bot):
    update = create_update("/status")
    context = ContextTypes.DEFAULT_TYPE.from_update(update, telegram_app)
    await telegram_app.process_update(update)
    messages = dummy_bot.sent_messages
    assert any("Your task progress" in text for (_, text) in messages), \
        "El mensaje de status no se envió"

@pytest.mark.asyncio
async def test_complete_task_command(dummy_bot):
    update = create_update("/complete_task STARTED")
    context = ContextTypes.DEFAULT_TYPE.from_update(update, telegram_app)
    await telegram_app.process_update(update)
    messages = dummy_bot.sent_messages
    assert any("marked complete" in text for (_, text) in messages), \
        "No se confirmó la tarea completada"

@pytest.mark.asyncio
async def test_add_wallet_conversation(dummy_bot):
    # Iniciar conversación con /add_wallet
    update = create_update("/add_wallet")
    context = ContextTypes.DEFAULT_TYPE.from_update(update, telegram_app)
    await telegram_app.process_update(update)
    # Enviar wallet address
    wallet_update = create_update("0x123456789abcdef")
    await telegram_app.process_update(wallet_update)
    messages = dummy_bot.sent_messages
    assert any("Wallet saved" in text for (_, text) in messages), \
        "No se registró la wallet correctamente"