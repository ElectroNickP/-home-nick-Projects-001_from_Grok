"""
Bot API routes for FastAPI application.

This module provides REST API endpoints for bot management operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ...usecases import BotManagementUseCase
from ..schemas import (
    BotCreateRequest, BotUpdateRequest, BotResponse, 
    BotListResponse, BotStatusResponse
)
from ...domain.entities import BotConfig


# Create router
bot_router = APIRouter()
bot_router.usecase: Optional[BotManagementUseCase] = None

logger = logging.getLogger(__name__)


@bot_router.get("/", response_model=BotListResponse)
async def list_bots():
    """List all bots."""
    try:
        bots = bot_router.usecase.get_all_bots()
        
        bot_responses = []
        for bot in bots:
            bot_responses.append(BotResponse(
                id=bot.id,
                name=bot.config.name,
                status=bot.status,
                message_count=bot.message_count,
                voice_message_count=bot.voice_message_count,
                created_at=bot.created_at,
                updated_at=bot.updated_at,
                last_error=bot.last_error
            ))
        
        return BotListResponse(
            bots=bot_responses,
            total=len(bot_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bots"
        )


@bot_router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: int):
    """Get bot by ID."""
    try:
        bot = bot_router.usecase.get_bot(bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {bot_id} not found"
            )
        
        return BotResponse(
            id=bot.id,
            name=bot.config.name,
            status=bot.status,
            message_count=bot.message_count,
            voice_message_count=bot.voice_message_count,
            created_at=bot.created_at,
            updated_at=bot.updated_at,
            last_error=bot.last_error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot"
        )


@bot_router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(bot_request: BotCreateRequest):
    """Create a new bot."""
    try:
        bot_config = BotConfig(
            name=bot_request.name,
            telegram_token=bot_request.telegram_token,
            openai_api_key=bot_request.openai_api_key,
            assistant_id=bot_request.assistant_id,
            group_context_limit=bot_request.group_context_limit,
            enable_ai_responses=bot_request.enable_ai_responses,
            enable_voice_responses=bot_request.enable_voice_responses,
            voice_model=bot_request.voice_model,
            voice_type=bot_request.voice_type,
        )
        
        bot_id = bot_router.usecase.create_bot(bot_config)
        bot = bot_router.usecase.get_bot(bot_id)
        
        return BotResponse(
            id=bot.id,
            name=bot.config.name,
            status=bot.status,
            message_count=bot.message_count,
            voice_message_count=bot.voice_message_count,
            created_at=bot.created_at,
            updated_at=bot.updated_at,
            last_error=bot.last_error
        )
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )


@bot_router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: int, bot_request: BotUpdateRequest):
    """Update bot configuration."""
    try:
        # Get current bot
        current_bot = bot_router.usecase.get_bot(bot_id)
        if not current_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {bot_id} not found"
            )
        
        # Update only provided fields
        config_data = current_bot.config.__dict__.copy()
        if bot_request.name is not None:
            config_data['name'] = bot_request.name
        if bot_request.telegram_token is not None:
            config_data['telegram_token'] = bot_request.telegram_token
        if bot_request.openai_api_key is not None:
            config_data['openai_api_key'] = bot_request.openai_api_key
        if bot_request.assistant_id is not None:
            config_data['assistant_id'] = bot_request.assistant_id
        if bot_request.group_context_limit is not None:
            config_data['group_context_limit'] = bot_request.group_context_limit
        if bot_request.enable_ai_responses is not None:
            config_data['enable_ai_responses'] = bot_request.enable_ai_responses
        if bot_request.enable_voice_responses is not None:
            config_data['enable_voice_responses'] = bot_request.enable_voice_responses
        if bot_request.voice_model is not None:
            config_data['voice_model'] = bot_request.voice_model
        if bot_request.voice_type is not None:
            config_data['voice_type'] = bot_request.voice_type
        
        bot_config = BotConfig(**config_data)
        success = bot_router.usecase.update_bot(bot_id, bot_config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update bot"
            )
        
        # Get updated bot
        updated_bot = bot_router.usecase.get_bot(bot_id)
        return BotResponse(
            id=updated_bot.id,
            name=updated_bot.config.name,
            status=updated_bot.status,
            message_count=updated_bot.message_count,
            voice_message_count=updated_bot.voice_message_count,
            created_at=updated_bot.created_at,
            updated_at=updated_bot.updated_at,
            last_error=updated_bot.last_error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot"
        )


@bot_router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(bot_id: int):
    """Delete a bot."""
    try:
        bot = bot_router.usecase.get_bot(bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {bot_id} not found"
            )
        
        success = bot_router.usecase.delete_bot(bot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete bot"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )


@bot_router.post("/{bot_id}/start", response_model=BotStatusResponse)
async def start_bot(bot_id: int):
    """Start a bot."""
    try:
        success = bot_router.usecase.start_bot(bot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start bot"
            )
        
        status_info = bot_router.usecase.get_bot_status(bot_id)
        return BotStatusResponse(
            id=bot_id,
            status=status_info,
            last_error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bot"
        )


@bot_router.post("/{bot_id}/stop", response_model=BotStatusResponse)
async def stop_bot(bot_id: int):
    """Stop a bot."""
    try:
        success = bot_router.usecase.stop_bot(bot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop bot"
            )
        
        status_info = bot_router.usecase.get_bot_status(bot_id)
        return BotStatusResponse(
            id=bot_id,
            status=status_info,
            last_error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop bot"
        )


@bot_router.post("/{bot_id}/restart", response_model=BotStatusResponse)
async def restart_bot(bot_id: int):
    """Restart a bot."""
    try:
        success = bot_router.usecase.restart_bot(bot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart bot"
            )
        
        status_info = bot_router.usecase.get_bot_status(bot_id)
        return BotStatusResponse(
            id=bot_id,
            status=status_info,
            last_error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart bot"
        )


@bot_router.get("/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(bot_id: int):
    """Get bot status."""
    try:
        status_info = bot_router.usecase.get_bot_status(bot_id)
        bot = bot_router.usecase.get_bot(bot_id)
        
        return BotStatusResponse(
            id=bot_id,
            status=status_info,
            last_error=bot.last_error if bot else None
        )
        
    except Exception as e:
        logger.error(f"Error getting bot status {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot status"
        )


@bot_router.get("/stats/summary")
async def get_bot_stats():
    """Get bot statistics."""
    try:
        total_bots = bot_router.usecase.get_bot_count()
        running_bots = bot_router.usecase.get_running_bot_count()
        stopped_bots = total_bots - running_bots
        
        return {
            "total_bots": total_bots,
            "running_bots": running_bots,
            "stopped_bots": stopped_bots,
            "running_percentage": (running_bots / total_bots * 100) if total_bots > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot statistics"
        )










