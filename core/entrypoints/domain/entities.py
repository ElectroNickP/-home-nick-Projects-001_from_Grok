"""
Domain entities imports for entry points.

This module provides convenient imports for domain entities used by entry points.
"""

from core.domain.bot import BotConfig, Bot, BotStatus
from core.domain.config import SystemConfig, AdminBotConfig
from core.domain.conversation import Conversation, Message

# Create ConversationKey as an alias for convenience
ConversationKey = str

__all__ = [
    'BotConfig',
    'Bot', 
    'BotStatus',
    'SystemConfig',
    'AdminBotConfig',
    'Conversation',
    'Message',
    'ConversationKey'
]







