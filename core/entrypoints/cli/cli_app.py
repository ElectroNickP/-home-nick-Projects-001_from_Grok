"""
CLI application for Telegram Bot Manager.

This module provides the command-line interface using Click framework.
"""

import logging
import sys

import click

from ..usecases import BotManagementUseCase, ConversationUseCase, SystemUseCase
from .commands import bot_group, conversation_group, system_group


class CLIApp:
    """CLI application for Telegram Bot Manager."""

    def __init__(
        self,
        bot_usecase: BotManagementUseCase,
        conversation_usecase: ConversationUseCase,
        system_usecase: SystemUseCase,
        config: dict | None = None,
    ):
        """Initialize CLI application with use cases."""
        self.bot_usecase = bot_usecase
        self.conversation_usecase = conversation_usecase
        self.system_usecase = system_usecase
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Configure logging
        self._configure_logging()

        # Pass use cases to command groups
        bot_group.usecase = self.bot_usecase
        system_group.usecase = self.system_usecase
        conversation_group.usecase = self.conversation_usecase

    def _configure_logging(self):
        """Configure logging for CLI."""
        log_level = self.config.get('log_level', 'INFO')
        verbose = self.config.get('verbose', False)

        if verbose:
            log_level = 'DEBUG'

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('cli.log')
            ]
        )

    def run(self, args: list | None = None):
        """Run CLI application."""
        try:
            cli(args=args)
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
            sys.exit(1)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose: bool, config: str | None):
    """Telegram Bot Manager CLI.
    
    A command-line interface for managing Telegram bots, conversations, and system settings.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store configuration in context
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config

    # Configure logging based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


# Add command groups
cli.add_command(bot_group)
cli.add_command(system_group)
cli.add_command(conversation_group)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    click.echo("Telegram Bot Manager CLI v1.0.0")
    click.echo("Built with hexagonal architecture")


@cli.command()
@click.pass_context
def status(ctx):
    """Show overall system status."""
    try:
        # Get system stats
        stats = system_group.usecase.get_system_stats()

        click.echo("=== System Status ===")
        click.echo(f"Total bots: {stats.get('total_bots', 0)}")
        click.echo(f"Running bots: {stats.get('running_bots', 0)}")
        click.echo(f"Stopped bots: {stats.get('stopped_bots', 0)}")
        click.echo(f"System uptime: {stats.get('uptime', 'Unknown')}")
        click.echo(f"Memory usage: {stats.get('memory_usage', 'Unknown')}")
        click.echo(f"CPU usage: {stats.get('cpu_usage', 'Unknown')}")

    except Exception as e:
        click.echo(f"Error getting system status: {e}", err=True)


@cli.command()
@click.pass_context
def info(ctx):
    """Show detailed system information."""
    try:
        # Get system config
        config = system_group.usecase.get_system_config()
        admin_config = system_group.usecase.get_admin_bot_config()

        click.echo("=== System Information ===")
        if config:
            click.echo(f"Auto update enabled: {config.auto_update_enabled}")
            click.echo(f"Backup enabled: {config.backup_enabled}")
            click.echo(f"Backup interval: {config.backup_interval_hours} hours")
            click.echo(f"Max backups: {config.max_backups}")
            click.echo(f"Log level: {config.log_level}")
            click.echo(f"Notification email: {config.notification_email}")

        if admin_config:
            click.echo(f"Admin bot enabled: {admin_config.enabled}")
            click.echo(f"Admin bot token: {'*' * len(admin_config.telegram_token) if admin_config.telegram_token else 'Not set'}")

    except Exception as e:
        click.echo(f"Error getting system information: {e}", err=True)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()









