"""
Conversation routes for Flask web application.

This module provides routes for conversation management operations.
"""

import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import BadRequest, NotFound

from ...domain.entities import ConversationKey
from ...usecases import ConversationUseCase

# Create blueprint
conversation_bp = Blueprint('conversations', __name__)
conversation_bp.usecase: ConversationUseCase | None = None

logger = logging.getLogger(__name__)


@conversation_bp.route('/', methods=['GET'])
def list_conversations():
    """List all conversations."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, we'll show a placeholder
        conversations = []
        return render_template('conversations/list.html', conversations=conversations)
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        flash('Error loading conversations', 'error')
        return render_template('conversations/list.html', conversations=[])


@conversation_bp.route('/<path:conversation_key>', methods=['GET'])
def get_conversation(conversation_key: str):
    """Get conversation details."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise BadRequest("Invalid conversation key format")

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        conversation = conversation_bp.usecase.get_conversation(conv_key)
        if not conversation:
            raise NotFound(f"Conversation {conversation_key} not found")

        return render_template('conversations/detail.html',
                             conversation=conversation,
                             conversation_key=conversation_key)
    except (BadRequest, ValueError) as e:
        flash(str(e), 'error')
        return redirect(url_for('conversations.list_conversations'))
    except NotFound:
        flash(f'Conversation {conversation_key} not found', 'error')
        return redirect(url_for('conversations.list_conversations'))
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_key}: {e}")
        flash('Error loading conversation', 'error')
        return redirect(url_for('conversations.list_conversations'))


@conversation_bp.route('/<path:conversation_key>/clear', methods=['POST'])
def clear_conversation(conversation_key: str):
    """Clear a conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            raise BadRequest("Invalid conversation key format")

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        success = conversation_bp.usecase.clear_conversation(conv_key)
        if success:
            flash('Conversation cleared successfully', 'success')
        else:
            flash('Failed to clear conversation', 'error')

    except (BadRequest, ValueError) as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Error clearing conversation {conversation_key}: {e}")
        flash('Error clearing conversation', 'error')

    return redirect(url_for('conversations.get_conversation', conversation_key=conversation_key))


# API endpoints for AJAX requests
@conversation_bp.route('/api/<path:conversation_key>', methods=['GET'])
def api_get_conversation(conversation_key: str):
    """API endpoint to get conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            return jsonify({
                'success': False,
                'error': 'Invalid conversation key format'
            }), 400

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        conversation = conversation_bp.usecase.get_conversation(conv_key)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404

        return jsonify({
            'success': True,
            'conversation': conversation.to_dict()
        })
    except (ValueError, BadRequest) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API error getting conversation {conversation_key}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get conversation'
        }), 500


@conversation_bp.route('/api/<path:conversation_key>/messages', methods=['GET'])
def api_get_messages(conversation_key: str):
    """API endpoint to get conversation messages."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            return jsonify({
                'success': False,
                'error': 'Invalid conversation key format'
            }), 400

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        # Get limit from query parameters
        limit = request.args.get('limit', type=int, default=50)

        messages = conversation_bp.usecase.get_recent_messages(conv_key, limit=limit)

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages]
        })
    except (ValueError, BadRequest) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API error getting messages for {conversation_key}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get messages'
        }), 500


@conversation_bp.route('/api/<path:conversation_key>/context', methods=['GET'])
def api_get_context(conversation_key: str):
    """API endpoint to get conversation context for AI."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            return jsonify({
                'success': False,
                'error': 'Invalid conversation key format'
            }), 400

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        context = conversation_bp.usecase.get_context_for_ai(conv_key)

        return jsonify({
            'success': True,
            'context': context
        })
    except (ValueError, BadRequest) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API error getting context for {conversation_key}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get context'
        }), 500


@conversation_bp.route('/api/<path:conversation_key>/clear', methods=['POST'])
def api_clear_conversation(conversation_key: str):
    """API endpoint to clear conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            return jsonify({
                'success': False,
                'error': 'Invalid conversation key format'
            }), 400

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        success = conversation_bp.usecase.clear_conversation(conv_key)

        return jsonify({
            'success': success,
            'message': 'Conversation cleared successfully' if success else 'Failed to clear conversation'
        })
    except (ValueError, BadRequest) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API error clearing conversation {conversation_key}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear conversation'
        }), 500








