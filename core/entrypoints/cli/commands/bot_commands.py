"""
Bot commands for CLI application.

This module provides Click commands for bot management operations.
"""

import logging

import click
from tabulate import tabulate

from ...domain.entities import BotConfig
from ...usecases import BotManagementUseCase

# Create command group
bot_group = click.Group('bot', help='Bot management commands')
bot_group.usecase: BotManagementUseCase | None = None

logger = logging.getLogger(__name__)


@bot_group.command('list')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list_bots(ctx, format: str):
    """List all bots."""
    try:
        bots = bot_group.usecase.get_all_bots()

        if not bots:
            click.echo("No bots found.")
            return

        if format == 'json':
            import json
            click.echo(json.dumps([bot.to_dict() for bot in bots], indent=2))
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Name', 'Status', 'Message Count', 'Voice Count', 'Created'])
            for bot in bots:
                writer.writerow([
                    bot.id,
                    bot.config.name,
                    bot.status,
                    bot.message_count,
                    bot.voice_message_count,
                    bot.created_at
                ])
            click.echo(output.getvalue())
        else:  # table format
            headers = ['ID', 'Name', 'Status', 'Messages', 'Voice', 'Created', 'Last Error']
            table_data = []
            for bot in bots:
                table_data.append([
                    bot.id,
                    bot.config.name,
                    bot.status,
                    bot.message_count,
                    bot.voice_message_count,
                    bot.created_at[:10] if bot.created_at else 'N/A',
                    bot.last_error[:30] + '...' if bot.last_error and len(bot.last_error) > 30 else bot.last_error or 'N/A'
                ])
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        click.echo(f"Error listing bots: {e}", err=True)


@bot_group.command('show')
@click.argument('bot_id', type=int)
@click.pass_context
def show_bot(ctx, bot_id: int):
    """Show bot details."""
    try:
        bot = bot_group.usecase.get_bot(bot_id)
        if not bot:
            click.echo(f"Bot {bot_id} not found.", err=True)
            return

        click.echo(f"=== Bot {bot_id} Details ===")
        click.echo(f"Name: {bot.config.name}")
        click.echo(f"Status: {bot.status}")
        click.echo(f"Telegram Token: {'*' * len(bot.config.telegram_token) if bot.config.telegram_token else 'Not set'}")
        click.echo(f"OpenAI API Key: {'*' * len(bot.config.openai_api_key) if bot.config.openai_api_key else 'Not set'}")
        click.echo(f"Assistant ID: {bot.config.assistant_id}")
        click.echo(f"Group Context Limit: {bot.config.group_context_limit}")
        click.echo(f"AI Responses Enabled: {bot.config.enable_ai_responses}")
        click.echo(f"Voice Responses Enabled: {bot.config.enable_voice_responses}")
        click.echo(f"Voice Model: {bot.config.voice_model}")
        click.echo(f"Voice Type: {bot.config.voice_type}")
        click.echo(f"Message Count: {bot.message_count}")
        click.echo(f"Voice Message Count: {bot.voice_message_count}")
        click.echo(f"Created: {bot.created_at}")
        click.echo(f"Updated: {bot.updated_at}")
        if bot.last_error:
            click.echo(f"Last Error: {bot.last_error}")

    except Exception as e:
        click.echo(f"Error showing bot {bot_id}: {e}", err=True)


@bot_group.command('create')
@click.option('--name', '-n', required=True, help='Bot name')
@click.option('--token', '-t', required=True, help='Telegram bot token')
@click.option('--openai-key', '-o', required=True, help='OpenAI API key')
@click.option('--assistant-id', '-a', required=True, help='OpenAI Assistant ID')
@click.option('--group-context', '-g', type=int, default=15, help='Group context limit')
@click.option('--ai-responses/--no-ai-responses', default=True, help='Enable AI responses')
@click.option('--voice-responses/--no-voice-responses', default=False, help='Enable voice responses')
@click.option('--voice-model', default='tts-1', help='Voice model')
@click.option('--voice-type', default='alloy', help='Voice type')
@click.pass_context
def create_bot(ctx, name: str, token: str, openai_key: str, assistant_id: str,
               group_context: int, ai_responses: bool, voice_responses: bool,
               voice_model: str, voice_type: str):
    """Create a new bot."""
    try:
        bot_config = BotConfig(
            name=name,
            telegram_token=token,
            openai_api_key=openai_key,
            assistant_id=assistant_id,
            group_context_limit=group_context,
            enable_ai_responses=ai_responses,
            enable_voice_responses=voice_responses,
            voice_model=voice_model,
            voice_type=voice_type,
        )

        bot_id = bot_group.usecase.create_bot(bot_config)
        click.echo(f"Bot '{name}' created successfully with ID {bot_id}")

    except Exception as e:
        click.echo(f"Error creating bot: {e}", err=True)


@bot_group.command('update')
@click.argument('bot_id', type=int)
@click.option('--name', '-n', help='Bot name')
@click.option('--token', '-t', help='Telegram bot token')
@click.option('--openai-key', '-o', help='OpenAI API key')
@click.option('--assistant-id', '-a', help='OpenAI Assistant ID')
@click.option('--group-context', '-g', type=int, help='Group context limit')
@click.option('--ai-responses/--no-ai-responses', help='Enable AI responses')
@click.option('--voice-responses/--no-voice-responses', help='Enable voice responses')
@click.option('--voice-model', help='Voice model')
@click.option('--voice-type', help='Voice type')
@click.pass_context
def update_bot(ctx, bot_id: int, name: str, token: str, openai_key: str, assistant_id: str,
               group_context: int, ai_responses: bool, voice_responses: bool,
               voice_model: str, voice_type: str):
    """Update bot configuration."""
    try:
        # Get current bot config
        current_bot = bot_group.usecase.get_bot(bot_id)
        if not current_bot:
            click.echo(f"Bot {bot_id} not found.", err=True)
            return

        # Update only provided fields
        config_data = current_bot.config.__dict__.copy()
        if name is not None:
            config_data['name'] = name
        if token is not None:
            config_data['telegram_token'] = token
        if openai_key is not None:
            config_data['openai_api_key'] = openai_key
        if assistant_id is not None:
            config_data['assistant_id'] = assistant_id
        if group_context is not None:
            config_data['group_context_limit'] = group_context
        if ai_responses is not None:
            config_data['enable_ai_responses'] = ai_responses
        if voice_responses is not None:
            config_data['enable_voice_responses'] = voice_responses
        if voice_model is not None:
            config_data['voice_model'] = voice_model
        if voice_type is not None:
            config_data['voice_type'] = voice_type

        bot_config = BotConfig(**config_data)
        success = bot_group.usecase.update_bot(bot_id, bot_config)

        if success:
            click.echo(f"Bot {bot_id} updated successfully")
        else:
            click.echo(f"Failed to update bot {bot_id}", err=True)

    except Exception as e:
        click.echo(f"Error updating bot {bot_id}: {e}", err=True)


@bot_group.command('delete')
@click.argument('bot_id', type=int)
@click.option('--force', '-f', is_flag=True, help='Force deletion without confirmation')
@click.pass_context
def delete_bot(ctx, bot_id: int, force: bool):
    """Delete a bot."""
    try:
        bot = bot_group.usecase.get_bot(bot_id)
        if not bot:
            click.echo(f"Bot {bot_id} not found.", err=True)
            return

        if not force:
            if not click.confirm(f"Are you sure you want to delete bot '{bot.config.name}' (ID: {bot_id})?"):
                click.echo("Deletion cancelled.")
                return

        success = bot_group.usecase.delete_bot(bot_id)
        if success:
            click.echo(f"Bot '{bot.config.name}' deleted successfully")
        else:
            click.echo(f"Failed to delete bot {bot_id}", err=True)

    except Exception as e:
        click.echo(f"Error deleting bot {bot_id}: {e}", err=True)


@bot_group.command('start')
@click.argument('bot_id', type=int)
@click.pass_context
def start_bot(ctx, bot_id: int):
    """Start a bot."""
    try:
        success = bot_group.usecase.start_bot(bot_id)
        if success:
            click.echo(f"Bot {bot_id} started successfully")
        else:
            click.echo(f"Failed to start bot {bot_id}", err=True)

    except Exception as e:
        click.echo(f"Error starting bot {bot_id}: {e}", err=True)


@bot_group.command('stop')
@click.argument('bot_id', type=int)
@click.pass_context
def stop_bot(ctx, bot_id: int):
    """Stop a bot."""
    try:
        success = bot_group.usecase.stop_bot(bot_id)
        if success:
            click.echo(f"Bot {bot_id} stopped successfully")
        else:
            click.echo(f"Failed to stop bot {bot_id}", err=True)

    except Exception as e:
        click.echo(f"Error stopping bot {bot_id}: {e}", err=True)


@bot_group.command('restart')
@click.argument('bot_id', type=int)
@click.pass_context
def restart_bot(ctx, bot_id: int):
    """Restart a bot."""
    try:
        success = bot_group.usecase.restart_bot(bot_id)
        if success:
            click.echo(f"Bot {bot_id} restarted successfully")
        else:
            click.echo(f"Failed to restart bot {bot_id}", err=True)

    except Exception as e:
        click.echo(f"Error restarting bot {bot_id}: {e}", err=True)


@bot_group.command('status')
@click.argument('bot_id', type=int)
@click.pass_context
def bot_status(ctx, bot_id: int):
    """Get bot status."""
    try:
        status = bot_group.usecase.get_bot_status(bot_id)
        click.echo(f"Bot {bot_id} status: {status}")

    except Exception as e:
        click.echo(f"Error getting bot {bot_id} status: {e}", err=True)


@bot_group.command('stats')
@click.pass_context
def bot_stats(ctx):
    """Show bot statistics."""
    try:
        total_bots = bot_group.usecase.get_bot_count()
        running_bots = bot_group.usecase.get_running_bot_count()
        stopped_bots = total_bots - running_bots

        click.echo("=== Bot Statistics ===")
        click.echo(f"Total bots: {total_bots}")
        click.echo(f"Running bots: {running_bots}")
        click.echo(f"Stopped bots: {stopped_bots}")

        if total_bots > 0:
            running_percentage = (running_bots / total_bots) * 100
            click.echo(f"Running percentage: {running_percentage:.1f}%")

    except Exception as e:
        click.echo(f"Error getting bot statistics: {e}", err=True)










