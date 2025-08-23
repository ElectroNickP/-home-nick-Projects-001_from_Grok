"""
Bot routes for Flask web application.

This module provides routes for bot management operations.
"""

import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import BadRequest, NotFound

from ...domain.entities import BotConfig
from ...usecases import BotManagementUseCase

# Create blueprint
bot_bp = Blueprint('bots', __name__)
bot_bp.usecase: BotManagementUseCase | None = None

logger = logging.getLogger(__name__)


@bot_bp.route('/', methods=['GET'])
def list_bots():
    """List all bots."""
    try:
        bots = bot_bp.usecase.get_all_bots()
        return render_template('bots/list.html', bots=bots)
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        flash('Error loading bots', 'error')
        return render_template('bots/list.html', bots=[])


@bot_bp.route('/<int:bot_id>', methods=['GET'])
def get_bot(bot_id: int):
    """Get bot details."""
    try:
        bot = bot_bp.usecase.get_bot(bot_id)
        if not bot:
            raise NotFound(f"Bot {bot_id} not found")
        return render_template('bots/detail.html', bot=bot)
    except NotFound:
        flash(f'Bot {bot_id} not found', 'error')
        return redirect(url_for('bots.list_bots'))
    except Exception as e:
        logger.error(f"Error getting bot {bot_id}: {e}")
        flash('Error loading bot', 'error')
        return redirect(url_for('bots.list_bots'))


@bot_bp.route('/create', methods=['GET', 'POST'])
def create_bot():
    """Create a new bot."""
    if request.method == 'GET':
        return render_template('bots/create.html')

    try:
        # Validate required fields
        required_fields = ['name', 'telegram_token', 'openai_api_key', 'assistant_id']
        data = {}
        for field in required_fields:
            value = request.form.get(field)
            if not value:
                raise BadRequest(f"Missing required field: {field}")
            data[field] = value

        # Optional fields
        data['group_context_limit'] = int(request.form.get('group_context_limit', 15))
        data['enable_ai_responses'] = request.form.get('enable_ai_responses') == 'on'
        data['enable_voice_responses'] = request.form.get('enable_voice_responses') == 'on'
        data['voice_model'] = request.form.get('voice_model', 'tts-1')
        data['voice_type'] = request.form.get('voice_type', 'alloy')

        # Create bot config
        bot_config = BotConfig(**data)

        # Create bot
        bot_id = bot_bp.usecase.create_bot(bot_config)

        flash(f'Bot "{bot_config.name}" created successfully', 'success')
        return redirect(url_for('bots.get_bot', bot_id=bot_id))

    except BadRequest as e:
        flash(str(e), 'error')
        return render_template('bots/create.html', form_data=request.form)
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        flash('Error creating bot', 'error')
        return render_template('bots/create.html', form_data=request.form)


@bot_bp.route('/<int:bot_id>/edit', methods=['GET', 'POST'])
def edit_bot(bot_id: int):
    """Edit bot configuration."""
    try:
        bot = bot_bp.usecase.get_bot(bot_id)
        if not bot:
            raise NotFound(f"Bot {bot_id} not found")

        if request.method == 'GET':
            return render_template('bots/edit.html', bot=bot)

        # Validate required fields
        required_fields = ['name', 'telegram_token', 'openai_api_key', 'assistant_id']
        data = {}
        for field in required_fields:
            value = request.form.get(field)
            if not value:
                raise BadRequest(f"Missing required field: {field}")
            data[field] = value

        # Optional fields
        data['group_context_limit'] = int(request.form.get('group_context_limit', 15))
        data['enable_ai_responses'] = request.form.get('enable_ai_responses') == 'on'
        data['enable_voice_responses'] = request.form.get('enable_voice_responses') == 'on'
        data['voice_model'] = request.form.get('voice_model', 'tts-1')
        data['voice_type'] = request.form.get('voice_type', 'alloy')

        # Create bot config
        bot_config = BotConfig(**data)

        # Update bot
        success = bot_bp.usecase.update_bot(bot_id, bot_config)
        if not success:
            raise Exception("Failed to update bot")

        flash(f'Bot "{bot_config.name}" updated successfully', 'success')
        return redirect(url_for('bots.get_bot', bot_id=bot_id))

    except NotFound:
        flash(f'Bot {bot_id} not found', 'error')
        return redirect(url_for('bots.list_bots'))
    except BadRequest as e:
        flash(str(e), 'error')
        return render_template('bots/edit.html', bot=bot)
    except Exception as e:
        logger.error(f"Error updating bot {bot_id}: {e}")
        flash('Error updating bot', 'error')
        return render_template('bots/edit.html', bot=bot)


@bot_bp.route('/<int:bot_id>/delete', methods=['POST'])
def delete_bot(bot_id: int):
    """Delete a bot."""
    try:
        bot = bot_bp.usecase.get_bot(bot_id)
        if not bot:
            raise NotFound(f"Bot {bot_id} not found")

        success = bot_bp.usecase.delete_bot(bot_id)
        if not success:
            raise Exception("Failed to delete bot")

        flash(f'Bot "{bot.config.name}" deleted successfully', 'success')
        return redirect(url_for('bots.list_bots'))

    except NotFound:
        flash(f'Bot {bot_id} not found', 'error')
        return redirect(url_for('bots.list_bots'))
    except Exception as e:
        logger.error(f"Error deleting bot {bot_id}: {e}")
        flash('Error deleting bot', 'error')
        return redirect(url_for('bots.list_bots'))


@bot_bp.route('/<int:bot_id>/start', methods=['POST'])
def start_bot(bot_id: int):
    """Start a bot."""
    try:
        success = bot_bp.usecase.start_bot(bot_id)
        if success:
            flash('Bot started successfully', 'success')
        else:
            flash('Failed to start bot', 'error')
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        flash('Error starting bot', 'error')

    return redirect(url_for('bots.get_bot', bot_id=bot_id))


@bot_bp.route('/<int:bot_id>/stop', methods=['POST'])
def stop_bot(bot_id: int):
    """Stop a bot."""
    try:
        success = bot_bp.usecase.stop_bot(bot_id)
        if success:
            flash('Bot stopped successfully', 'success')
        else:
            flash('Failed to stop bot', 'error')
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        flash('Error stopping bot', 'error')

    return redirect(url_for('bots.get_bot', bot_id=bot_id))


@bot_bp.route('/<int:bot_id>/restart', methods=['POST'])
def restart_bot(bot_id: int):
    """Restart a bot."""
    try:
        success = bot_bp.usecase.restart_bot(bot_id)
        if success:
            flash('Bot restarted successfully', 'success')
        else:
            flash('Failed to restart bot', 'error')
    except Exception as e:
        logger.error(f"Error restarting bot {bot_id}: {e}")
        flash('Error restarting bot', 'error')

    return redirect(url_for('bots.get_bot', bot_id=bot_id))


# API endpoints for AJAX requests
@bot_bp.route('/api/list', methods=['GET'])
def api_list_bots():
    """API endpoint to list bots."""
    try:
        bots = bot_bp.usecase.get_all_bots()
        return jsonify({
            'success': True,
            'bots': [bot.to_dict() for bot in bots]
        })
    except Exception as e:
        logger.error(f"API error listing bots: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load bots'
        }), 500


@bot_bp.route('/api/<int:bot_id>/status', methods=['GET'])
def api_bot_status(bot_id: int):
    """API endpoint to get bot status."""
    try:
        status = bot_bp.usecase.get_bot_status(bot_id)
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"API error getting bot status {bot_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get bot status'
        }), 500


@bot_bp.route('/api/stats', methods=['GET'])
def api_bot_stats():
    """API endpoint to get bot statistics."""
    try:
        total_bots = bot_bp.usecase.get_bot_count()
        running_bots = bot_bp.usecase.get_running_bot_count()

        return jsonify({
            'success': True,
            'stats': {
                'total_bots': total_bots,
                'running_bots': running_bots,
                'stopped_bots': total_bots - running_bots
            }
        })
    except Exception as e:
        logger.error(f"API error getting bot stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get bot statistics'
        }), 500










