"""
Conversation schemas for FastAPI application.

This module contains Pydantic models for conversation-related API requests and responses.
"""


from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Response model for message data."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    bot_id: int = Field(..., description="Bot ID")
    user_id: int = Field(..., description="User ID")
    messages: list[MessageResponse] = Field(..., description="List of messages")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""
    conversations: list[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")








