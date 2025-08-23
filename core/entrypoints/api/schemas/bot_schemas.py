"""
Bot schemas for FastAPI application.

This module contains Pydantic models for bot-related API requests and responses.
"""


from pydantic import BaseModel, Field


class BotCreateRequest(BaseModel):
    """Request model for creating a bot."""
    name: str = Field(..., description="Bot name")
    telegram_token: str = Field(..., description="Telegram bot token")
    openai_api_key: str = Field(..., description="OpenAI API key")
    assistant_id: str = Field(..., description="OpenAI Assistant ID")
    group_context_limit: int = Field(default=15, description="Group context limit")
    enable_ai_responses: bool = Field(default=True, description="Enable AI responses")
    enable_voice_responses: bool = Field(default=False, description="Enable voice responses")
    voice_model: str = Field(default="tts-1", description="Voice model")
    voice_type: str = Field(default="alloy", description="Voice type")


class BotUpdateRequest(BaseModel):
    """Request model for updating a bot."""
    name: str | None = Field(None, description="Bot name")
    telegram_token: str | None = Field(None, description="Telegram bot token")
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    assistant_id: str | None = Field(None, description="OpenAI Assistant ID")
    group_context_limit: int | None = Field(None, description="Group context limit")
    enable_ai_responses: bool | None = Field(None, description="Enable AI responses")
    enable_voice_responses: bool | None = Field(None, description="Enable voice responses")
    voice_model: str | None = Field(None, description="Voice model")
    voice_type: str | None = Field(None, description="Voice type")


class BotResponse(BaseModel):
    """Response model for bot data."""
    id: int = Field(..., description="Bot ID")
    name: str = Field(..., description="Bot name")
    status: str = Field(..., description="Bot status")
    message_count: int = Field(..., description="Message count")
    voice_message_count: int = Field(..., description="Voice message count")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_error: str | None = Field(None, description="Last error message")


class BotListResponse(BaseModel):
    """Response model for bot list."""
    bots: list[BotResponse] = Field(..., description="List of bots")
    total: int = Field(..., description="Total number of bots")


class BotStatusResponse(BaseModel):
    """Response model for bot status."""
    id: int = Field(..., description="Bot ID")
    status: str = Field(..., description="Bot status")
    last_error: str | None = Field(None, description="Last error message")









