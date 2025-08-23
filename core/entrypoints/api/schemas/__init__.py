"""
API schemas for FastAPI application.

This module contains Pydantic models for request/response validation.
"""

# Import specific schemas to avoid star imports
from .bot_schemas import (
    BotCreateRequest,
    BotListResponse,
    BotResponse,
    BotStatusResponse,
    BotUpdateRequest,
)
from .conversation_schemas import (
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from .system_schemas import (
    BackupResponse,
    SystemConfigRequest,
    SystemConfigResponse,
    SystemStatusResponse,
    UpdateResponse,
)

__all__ = [
    # Bot schemas
    "BotCreateRequest",
    "BotUpdateRequest",
    "BotResponse",
    "BotListResponse",
    "BotStatusResponse",
    # Conversation schemas
    "ConversationResponse",
    "ConversationListResponse",
    "MessageResponse",
    # System schemas
    "SystemConfigRequest",
    "SystemConfigResponse",
    "SystemStatusResponse",
    "BackupResponse",
    "UpdateResponse",
]
