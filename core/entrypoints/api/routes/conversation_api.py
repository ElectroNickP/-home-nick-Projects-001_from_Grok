"""
Conversation API routes for FastAPI application.

This module provides REST API endpoints for conversation management operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query

from ...usecases import ConversationUseCase
from ..schemas import (
    ConversationResponse, ConversationListResponse, MessageResponse
)
from ...domain.entities import ConversationKey


# Create router
conversation_router = APIRouter()
conversation_router.usecase: Optional[ConversationUseCase] = None

logger = logging.getLogger(__name__)


@conversation_router.get("/", response_model=ConversationListResponse)
async def list_conversations():
    """List all conversations."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, return empty list
        conversations = []
        
        conversation_responses = []
        for conv in conversations:
            conversation_responses.append(ConversationResponse(
                bot_id=conv.get('bot_id', 0),
                user_id=conv.get('user_id', 0),
                messages=[],  # Would need to get actual messages
                created_at=conv.get('created_at', ''),
                updated_at=conv.get('updated_at', '')
            ))
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=len(conversation_responses)
        )
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )


@conversation_router.get("/{conversation_key}", response_model=ConversationResponse)
async def get_conversation(conversation_key: str):
    """Get conversation by key."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation key format. Use 'bot_id:user_id'"
            )
        
        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)
        
        conversation = conversation_router.usecase.get_conversation(conv_key)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_key} not found"
            )
        
        # Convert messages to response format
        messages = []
        for msg in conversation.messages:
            messages.append(MessageResponse(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))
        
        return ConversationResponse(
            bot_id=conversation.bot_id,
            user_id=conversation.user_id,
            messages=messages,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation key: {e}"
        )
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@conversation_router.get("/{conversation_key}/messages")
async def get_conversation_messages(
    conversation_key: str,
    limit: int = Query(default=50, ge=1, le=100, description="Number of messages to return")
):
    """Get conversation messages."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation key format. Use 'bot_id:user_id'"
            )
        
        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)
        
        messages = conversation_router.usecase.get_recent_messages(conv_key, limit=limit)
        
        message_responses = []
        for msg in messages:
            message_responses.append(MessageResponse(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))
        
        return {
            "conversation_key": conversation_key,
            "messages": message_responses,
            "total": len(message_responses)
        }
        
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation key: {e}"
        )
    except Exception as e:
        logger.error(f"Error getting messages for {conversation_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation messages"
        )


@conversation_router.get("/{conversation_key}/context")
async def get_conversation_context(conversation_key: str):
    """Get conversation context for AI."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation key format. Use 'bot_id:user_id'"
            )
        
        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)
        
        context = conversation_router.usecase.get_context_for_ai(conv_key)
        
        return {
            "conversation_key": conversation_key,
            "context": context
        }
        
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation key: {e}"
        )
    except Exception as e:
        logger.error(f"Error getting context for {conversation_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation context"
        )


@conversation_router.delete("/{conversation_key}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_conversation(conversation_key: str):
    """Clear a conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation key format. Use 'bot_id:user_id'"
            )
        
        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)
        
        success = conversation_router.usecase.clear_conversation(conv_key)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear conversation"
            )
        
        return None
        
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation key: {e}"
        )
    except Exception as e:
        logger.error(f"Error clearing conversation {conversation_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation"
        )


@conversation_router.get("/{conversation_key}/last-message")
async def get_last_message(conversation_key: str):
    """Get last message in conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation key format. Use 'bot_id:user_id'"
            )
        
        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)
        
        message = conversation_router.usecase.get_last_message(conv_key)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No messages found in conversation"
            )
        
        return MessageResponse(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp
        )
        
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation key: {e}"
        )
    except Exception as e:
        logger.error(f"Error getting last message for {conversation_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get last message"
        )


@conversation_router.get("/stats/summary")
async def get_conversation_stats():
    """Get conversation statistics."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, return placeholder data
        return {
            "total_conversations": 0,
            "active_conversations": 0,
            "total_messages": 0,
            "average_messages_per_conversation": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation statistics"
        )








