"""
Contract tests for TelegramPort interface.

Tests that verify any Telegram adapter correctly implements the TelegramPort contract.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from core.ports.telegram import TelegramPort


class MockTelegramAdapter(TelegramPort):
    """Mock implementation of TelegramPort for testing."""

    def __init__(self):
        self.mock_bot = Mock()
        self.mock_bot.send_message = AsyncMock(return_value=Mock(message_id="123"))
        self.mock_bot.send_voice = AsyncMock(return_value=Mock(message_id="456"))
        self.mock_bot.get_me = AsyncMock(return_value={"id": 123, "username": "test_bot"})
        self.mock_bot.validate_token = AsyncMock(return_value=True)
        self.mock_bot.get_updates = AsyncMock(return_value=[])
        self.mock_bot.answer_callback_query = AsyncMock()
        self.mock_bot.edit_message_text = AsyncMock()

    async def set_webhook(self, url: str, secret: str | None = None) -> None:
        """Mock webhook setting."""
        pass

    async def send_message(self, chat_id: str, text: str, **opts: Any) -> str:
        """Mock message sending."""
        result = await self.mock_bot.send_message(chat_id, text, **opts)
        return str(result.message_id)

    async def send_voice(self, chat_id: str, source: str, **opts: Any) -> str:
        """Mock voice sending."""
        result = await self.mock_bot.send_voice(chat_id, source, **opts)
        return str(result.message_id)

    async def get_me(self) -> dict[str, Any]:
        """Mock get bot info."""
        return await self.mock_bot.get_me()

    async def validate_token(self, token: str) -> bool:
        """Mock token validation."""
        return await self.mock_bot.validate_token(token)

    async def get_updates(
        self, offset: int | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Mock get updates."""
        return await self.mock_bot.get_updates(offset, limit)

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> None:
        """Mock answer callback query."""
        await self.mock_bot.answer_callback_query(callback_query_id, text)

    async def edit_message_text(
        self, chat_id: str, message_id: str, text: str, **opts: Any
    ) -> None:
        """Mock edit message text."""
        await self.mock_bot.edit_message_text(chat_id, message_id, text, **opts)


@pytest.fixture
def telegram_adapter() -> TelegramPort:
    """Provide a mock Telegram adapter for testing."""
    return MockTelegramAdapter()


@pytest.mark.asyncio
async def test_set_webhook_contract(telegram_adapter: TelegramPort):
    """Test that set_webhook method exists and can be called."""
    # Should not raise any exceptions
    await telegram_adapter.set_webhook("https://example.com/webhook")
    await telegram_adapter.set_webhook("https://example.com/webhook", "secret123")


@pytest.mark.asyncio
async def test_send_message_contract(telegram_adapter: TelegramPort):
    """Test that send_message method returns message ID."""
    msg_id = await telegram_adapter.send_message("123456", "Hello, world!")

    assert isinstance(msg_id, str)
    assert msg_id == "123"

    # Test with additional options
    msg_id = await telegram_adapter.send_message(
        "123456", "Hello with options", parse_mode="HTML", reply_markup={"keyboard": [["Button"]]}
    )
    assert isinstance(msg_id, str)


@pytest.mark.asyncio
async def test_send_voice_contract(telegram_adapter: TelegramPort):
    """Test that send_voice method returns message ID."""
    msg_id = await telegram_adapter.send_voice("123456", "/path/to/voice.ogg")

    assert isinstance(msg_id, str)
    assert msg_id == "456"

    # Test with additional options
    msg_id = await telegram_adapter.send_voice(
        "123456", "/path/to/voice.ogg", caption="Voice message", duration=30
    )
    assert isinstance(msg_id, str)


@pytest.mark.asyncio
async def test_get_me_contract(telegram_adapter: TelegramPort):
    """Test that get_me method returns bot information."""
    bot_info = await telegram_adapter.get_me()

    assert isinstance(bot_info, dict)
    assert "id" in bot_info
    assert "username" in bot_info
    assert bot_info["id"] == 123
    assert bot_info["username"] == "test_bot"


@pytest.mark.asyncio
async def test_validate_token_contract(telegram_adapter: TelegramPort):
    """Test that validate_token method returns boolean."""
    is_valid = await telegram_adapter.validate_token("valid_token_123")

    assert isinstance(is_valid, bool)
    assert is_valid is True


@pytest.mark.asyncio
async def test_get_updates_contract(telegram_adapter: TelegramPort):
    """Test that get_updates method returns list of updates."""
    updates = await telegram_adapter.get_updates()

    assert isinstance(updates, list)

    # Test with offset and limit
    updates = await telegram_adapter.get_updates(offset=100, limit=50)
    assert isinstance(updates, list)


@pytest.mark.asyncio
async def test_answer_callback_query_contract(telegram_adapter: TelegramPort):
    """Test that answer_callback_query method can be called."""
    # Should not raise any exceptions
    await telegram_adapter.answer_callback_query("callback_123")
    await telegram_adapter.answer_callback_query("callback_123", "Answer text")


@pytest.mark.asyncio
async def test_edit_message_text_contract(telegram_adapter: TelegramPort):
    """Test that edit_message_text method can be called."""
    # Should not raise any exceptions
    await telegram_adapter.edit_message_text("123456", "789", "Updated text")
    await telegram_adapter.edit_message_text(
        "123456", "789", "Updated text with options", parse_mode="HTML"
    )


def test_telegram_port_contract():
    """Main contract test function."""
    # This function can be used to run all contract tests
    # or to verify that an adapter implements all required methods
    adapter = MockTelegramAdapter()

    # Verify all required methods exist
    required_methods = [
        "set_webhook",
        "send_message",
        "send_voice",
        "get_me",
        "validate_token",
        "get_updates",
        "answer_callback_query",
        "edit_message_text",
    ]

    for method_name in required_methods:
        assert hasattr(adapter, method_name), f"Missing method: {method_name}"
        method = getattr(adapter, method_name)
        assert callable(method), f"Method {method_name} is not callable"








