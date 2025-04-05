import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Bot
from bot import telegram_app

# --- Helper function to create a simulated Update object ---
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
    # Use a real Bot instance with minimal configuration for de_json
    mock_bot = Bot(token="123:FAKE_TOKEN")
    return Update.de_json(update_dict, bot=mock_bot)

# --- Test for the /start command ---
@pytest.mark.asyncio
async def test_start_command():
    # Mock the entire bot object
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.initialize = AsyncMock()  # Mock the initialize method

    # Replace the bot in telegram_app with the mock bot
    with patch.object(telegram_app, "bot", mock_bot):
        # Initialize the telegram_app
        await telegram_app.initialize()

        # Create a simulated /start command update
        update = create_update("/start")

        # Process the update
        await telegram_app.process_update(update)

        # Assert that send_message was called
        try:
            mock_bot.send_message.assert_called_once()
        except AssertionError as e:
            print(f"Debug: mock_bot.send_message.call_args_list = {mock_bot.send_message.call_args_list}")
            raise e

        # Check the content of the message
        sent_message = mock_bot.send_message.call_args[1]["text"]
        assert "Welcome" in sent_message or "best Crypto Bot" in sent_message, \
            "The welcome message was not sent correctly"

        # Shutdown the telegram_app after the test
        await telegram_app.shutdown()