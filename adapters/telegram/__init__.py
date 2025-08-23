"""
Telegram adapters for hexagonal architecture.

This module contains implementations of TelegramPort interface
that interact with external Telegram Bot API.
"""

from .aiogram_adapter import AiogramTelegramAdapter

__all__ = [
    "AiogramTelegramAdapter",
]









