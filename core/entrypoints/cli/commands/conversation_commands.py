"""
Conversation commands for CLI application.

This module provides Click commands for conversation management operations.
"""

import logging

import click
from tabulate import tabulate

from ...domain.entities import ConversationKey
from ...usecases import ConversationUseCase

# Create command group
conversation_group = click.Group('conversation', help='Conversation management commands')
conversation_group.usecase: ConversationUseCase | None = None

logger = logging.getLogger(__name__)


@conversation_group.command('list')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list_conversations(ctx, format: str):
    """List all conversations."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, we'll show a placeholder
        conversations = []

        if not conversations:
            click.echo("No conversations found.")
            return

        if format == 'json':
            import json
            click.echo(json.dumps(conversations, indent=2))
        else:
            headers = ['Bot ID', 'User ID', 'Message Count', 'Last Message', 'Created']
            table_data = []
            for conv in conversations:
                table_data.append([
                    conv.get('bot_id', 'N/A'),
                    conv.get('user_id', 'N/A'),
                    conv.get('message_count', 0),
                    conv.get('last_message', 'N/A'),
                    conv.get('created', 'N/A')
                ])
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        click.echo(f"Error listing conversations: {e}", err=True)


@conversation_group.command('show')
@click.argument('conversation_key')
@click.option('--limit', '-l', type=int, default=50, help='Number of messages to show')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def show_conversation(ctx, conversation_key: str, limit: int, format: str):
    """Show conversation details."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            click.echo("Invalid conversation key format. Use 'bot_id:user_id'", err=True)
            return

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        conversation = conversation_group.usecase.get_conversation(conv_key)
        if not conversation:
            click.echo(f"Conversation {conversation_key} not found.", err=True)
            return

        if format == 'json':
            import json
            click.echo(json.dumps(conversation.to_dict(), indent=2))
        else:
            click.echo(f"=== Conversation {conversation_key} ===")
            click.echo(f"Bot ID: {conversation.bot_id}")
            click.echo(f"User ID: {conversation.user_id}")
            click.echo(f"Message count: {len(conversation.messages)}")
            click.echo(f"Created: {conversation.created_at}")
            click.echo(f"Updated: {conversation.updated_at}")

            # Show recent messages
            recent_messages = conversation_group.usecase.get_recent_messages(conv_key, limit=limit)
            if recent_messages:
                click.echo(f"\n=== Recent Messages (last {len(recent_messages)}) ===")
                headers = ['Role', 'Content', 'Timestamp']
                table_data = []
                for msg in recent_messages:
                    table_data.append([
                        msg.role,
                        msg.content[:50] + '...' if len(msg.content) > 50 else msg.content,
                        msg.timestamp
                    ])
                click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except (ValueError, TypeError) as e:
        click.echo(f"Invalid conversation key: {e}", err=True)
    except Exception as e:
        click.echo(f"Error showing conversation {conversation_key}: {e}", err=True)


@conversation_group.command('clear')
@click.argument('conversation_key')
@click.option('--force', '-f', is_flag=True, help='Force clearing without confirmation')
@click.pass_context
def clear_conversation(ctx, conversation_key: str, force: bool):
    """Clear a conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            click.echo("Invalid conversation key format. Use 'bot_id:user_id'", err=True)
            return

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        if not force:
            if not click.confirm(f"Are you sure you want to clear conversation {conversation_key}?"):
                click.echo("Clearing cancelled.")
                return

        success = conversation_group.usecase.clear_conversation(conv_key)
        if success:
            click.echo(f"Conversation {conversation_key} cleared successfully")
        else:
            click.echo(f"Failed to clear conversation {conversation_key}", err=True)

    except (ValueError, TypeError) as e:
        click.echo(f"Invalid conversation key: {e}", err=True)
    except Exception as e:
        click.echo(f"Error clearing conversation {conversation_key}: {e}", err=True)


@conversation_group.command('context')
@click.argument('conversation_key')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.pass_context
def get_context(ctx, conversation_key: str, format: str):
    """Get conversation context for AI."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            click.echo("Invalid conversation key format. Use 'bot_id:user_id'", err=True)
            return

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        context = conversation_group.usecase.get_context_for_ai(conv_key)

        if format == 'json':
            import json
            click.echo(json.dumps(context, indent=2))
        else:
            click.echo(f"=== AI Context for Conversation {conversation_key} ===")
            click.echo(context)

    except (ValueError, TypeError) as e:
        click.echo(f"Invalid conversation key: {e}", err=True)
    except Exception as e:
        click.echo(f"Error getting context for {conversation_key}: {e}", err=True)


@conversation_group.command('messages')
@click.argument('conversation_key')
@click.option('--limit', '-l', type=int, default=20, help='Number of messages to show')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def get_messages(ctx, conversation_key: str, limit: int, format: str):
    """Get conversation messages."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            click.echo("Invalid conversation key format. Use 'bot_id:user_id'", err=True)
            return

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        messages = conversation_group.usecase.get_recent_messages(conv_key, limit=limit)

        if not messages:
            click.echo("No messages found.")
            return

        if format == 'json':
            import json
            click.echo(json.dumps([msg.to_dict() for msg in messages], indent=2))
        else:
            click.echo(f"=== Messages for Conversation {conversation_key} ===")
            headers = ['Role', 'Content', 'Timestamp']
            table_data = []
            for msg in messages:
                table_data.append([
                    msg.role,
                    msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                    msg.timestamp
                ])
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except (ValueError, TypeError) as e:
        click.echo(f"Invalid conversation key: {e}", err=True)
    except Exception as e:
        click.echo(f"Error getting messages for {conversation_key}: {e}", err=True)


@conversation_group.command('last-message')
@click.argument('conversation_key')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.pass_context
def get_last_message(ctx, conversation_key: str, format: str):
    """Get last message in conversation."""
    try:
        # Parse conversation key
        key_parts = conversation_key.split(':')
        if len(key_parts) != 2:
            click.echo("Invalid conversation key format. Use 'bot_id:user_id'", err=True)
            return

        bot_id, user_id = int(key_parts[0]), int(key_parts[1])
        conv_key = ConversationKey(bot_id=bot_id, user_id=user_id)

        message = conversation_group.usecase.get_last_message(conv_key)

        if not message:
            click.echo("No messages found in conversation.")
            return

        if format == 'json':
            import json
            click.echo(json.dumps(message.to_dict(), indent=2))
        else:
            click.echo(f"=== Last Message in Conversation {conversation_key} ===")
            click.echo(f"Role: {message.role}")
            click.echo(f"Content: {message.content}")
            click.echo(f"Timestamp: {message.timestamp}")

    except (ValueError, TypeError) as e:
        click.echo(f"Invalid conversation key: {e}", err=True)
    except Exception as e:
        click.echo(f"Error getting last message for {conversation_key}: {e}", err=True)


@conversation_group.command('stats')
@click.pass_context
def conversation_stats(ctx):
    """Show conversation statistics."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, we'll show a placeholder
        click.echo("=== Conversation Statistics ===")
        click.echo("Total conversations: 0")
        click.echo("Active conversations: 0")
        click.echo("Total messages: 0")
        click.echo("Average messages per conversation: 0")
        click.echo("Conversation statistics not implemented yet")

    except Exception as e:
        click.echo(f"Error getting conversation statistics: {e}", err=True)










