"""
System commands for CLI application.

This module provides Click commands for system management operations.
"""

import logging

import click
from tabulate import tabulate

from ...usecases import SystemUseCase

# Create command group
system_group = click.Group('system', help='System management commands')
system_group.usecase: SystemUseCase | None = None

logger = logging.getLogger(__name__)


@system_group.command('status')
@click.pass_context
def system_status(ctx):
    """Show system status."""
    try:
        stats = system_group.usecase.get_system_stats()

        click.echo("=== System Status ===")
        click.echo(f"Total bots: {stats.get('total_bots', 0)}")
        click.echo(f"Running bots: {stats.get('running_bots', 0)}")
        click.echo(f"Stopped bots: {stats.get('stopped_bots', 0)}")
        click.echo(f"System uptime: {stats.get('uptime', 'Unknown')}")
        click.echo(f"Memory usage: {stats.get('memory_usage', 'Unknown')}")
        click.echo(f"CPU usage: {stats.get('cpu_usage', 'Unknown')}")
        click.echo(f"Disk usage: {stats.get('disk_usage', 'Unknown')}")
        click.echo(f"Network connections: {stats.get('network_connections', 'Unknown')}")

    except Exception as e:
        click.echo(f"Error getting system status: {e}", err=True)


@system_group.command('config')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def system_config(ctx, format: str):
    """Show system configuration."""
    try:
        config = system_group.usecase.get_system_config()
        admin_config = system_group.usecase.get_admin_bot_config()

        if format == 'json':
            import json
            output = {
                'system_config': config.to_dict() if config else None,
                'admin_config': admin_config.to_dict() if admin_config else None
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("=== System Configuration ===")
            if config:
                click.echo(f"Auto update enabled: {config.auto_update_enabled}")
                click.echo(f"Backup enabled: {config.backup_enabled}")
                click.echo(f"Backup interval: {config.backup_interval_hours} hours")
                click.echo(f"Max backups: {config.max_backups}")
                click.echo(f"Log level: {config.log_level}")
                click.echo(f"Notification email: {config.notification_email}")
            else:
                click.echo("No system configuration found")

            click.echo("\n=== Admin Bot Configuration ===")
            if admin_config:
                click.echo(f"Admin bot enabled: {admin_config.enabled}")
                click.echo(f"Admin bot token: {'*' * len(admin_config.telegram_token) if admin_config.telegram_token else 'Not set'}")
                click.echo(f"Admin bot username: {admin_config.username}")
                click.echo(f"Admin bot webhook: {admin_config.webhook_url}")
            else:
                click.echo("No admin bot configuration found")

    except Exception as e:
        click.echo(f"Error getting system configuration: {e}", err=True)


@system_group.command('backup')
@click.option('--force', '-f', is_flag=True, help='Force backup creation')
@click.pass_context
def create_backup(ctx, force: bool):
    """Create system backup."""
    try:
        if not force:
            if not click.confirm("Are you sure you want to create a backup?"):
                click.echo("Backup creation cancelled.")
                return

        backup_path = system_group.usecase.create_backup()
        if backup_path:
            click.echo(f"Backup created successfully: {backup_path}")
        else:
            click.echo("Failed to create backup", err=True)

    except Exception as e:
        click.echo(f"Error creating backup: {e}", err=True)


@system_group.command('backups')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list_backups(ctx, format: str):
    """List system backups."""
    try:
        backups = system_group.usecase.list_backups()

        if not backups:
            click.echo("No backups found.")
            return

        if format == 'json':
            import json
            click.echo(json.dumps(backups, indent=2))
        else:
            headers = ['Filename', 'Size', 'Created', 'Status']
            table_data = []
            for backup in backups:
                table_data.append([
                    backup.get('filename', 'N/A'),
                    backup.get('size', 'N/A'),
                    backup.get('created', 'N/A'),
                    backup.get('status', 'N/A')
                ])
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        click.echo(f"Error listing backups: {e}", err=True)


@system_group.command('restore')
@click.argument('backup_file')
@click.option('--force', '-f', is_flag=True, help='Force restoration without confirmation')
@click.pass_context
def restore_backup(ctx, backup_file: str, force: bool):
    """Restore system from backup."""
    try:
        if not force:
            if not click.confirm(f"Are you sure you want to restore from backup '{backup_file}'? This will overwrite current configuration."):
                click.echo("Restoration cancelled.")
                return

        success = system_group.usecase.restore_backup(backup_file)
        if success:
            click.echo(f"System restored successfully from {backup_file}")
        else:
            click.echo("Failed to restore system", err=True)

    except Exception as e:
        click.echo(f"Error restoring system: {e}", err=True)


@system_group.command('update')
@click.option('--force', '-f', is_flag=True, help='Force update without confirmation')
@click.pass_context
def apply_update(ctx, force: bool):
    """Apply system update."""
    try:
        if not force:
            if not click.confirm("Are you sure you want to apply system update? This may restart services."):
                click.echo("Update cancelled.")
                return

        success = system_group.usecase.apply_update()
        if success:
            click.echo("System update applied successfully")
        else:
            click.echo("Failed to apply system update", err=True)

    except Exception as e:
        click.echo(f"Error applying update: {e}", err=True)


@system_group.command('check-update')
@click.pass_context
def check_update(ctx):
    """Check for available updates."""
    try:
        update_info = system_group.usecase.check_updates()
        if update_info:
            click.echo("=== Available Updates ===")
            click.echo(f"Current version: {update_info.get('current_version', 'Unknown')}")
            click.echo(f"Latest version: {update_info.get('latest_version', 'Unknown')}")
            click.echo(f"Update available: {update_info.get('update_available', False)}")
            if update_info.get('changelog'):
                click.echo(f"Changelog: {update_info['changelog']}")
        else:
            click.echo("No update information available")

    except Exception as e:
        click.echo(f"Error checking for updates: {e}", err=True)


@system_group.command('logs')
@click.option('--lines', '-n', type=int, default=50, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), help='Log level filter')
@click.pass_context
def show_logs(ctx, lines: int, follow: bool, level: str):
    """Show system logs."""
    try:
        # Note: This would need to be implemented in the use case
        # For now, we'll show a placeholder
        click.echo(f"Showing last {lines} log lines...")
        if level:
            click.echo(f"Filtering by level: {level}")
        if follow:
            click.echo("Following log output (Ctrl+C to stop)...")

        # Placeholder for actual log reading
        click.echo("Log reading not implemented yet")

    except Exception as e:
        click.echo(f"Error reading logs: {e}", err=True)


@system_group.command('cleanup')
@click.option('--force', '-f', is_flag=True, help='Force cleanup without confirmation')
@click.pass_context
def cleanup_backups(ctx, force: bool):
    """Clean up old backups."""
    try:
        if not force:
            if not click.confirm("Are you sure you want to clean up old backups?"):
                click.echo("Cleanup cancelled.")
                return

        # Note: This would need to be implemented in the use case
        success = system_group.usecase.cleanup_old_backups()
        if success:
            click.echo("Old backups cleaned up successfully")
        else:
            click.echo("Failed to clean up old backups", err=True)

    except Exception as e:
        click.echo(f"Error cleaning up backups: {e}", err=True)


@system_group.command('validate')
@click.pass_context
def validate_system(ctx):
    """Validate system configuration."""
    try:
        click.echo("=== System Validation ===")

        # Check system config
        config = system_group.usecase.get_system_config()
        if config:
            click.echo("✓ System configuration loaded")
        else:
            click.echo("✗ System configuration not found")

        # Check admin bot config
        admin_config = system_group.usecase.get_admin_bot_config()
        if admin_config:
            click.echo("✓ Admin bot configuration loaded")
        else:
            click.echo("✗ Admin bot configuration not found")

        # Check system stats
        try:
            stats = system_group.usecase.get_system_stats()
            click.echo("✓ System statistics available")
        except Exception:
            click.echo("✗ System statistics not available")

        click.echo("System validation completed")

    except Exception as e:
        click.echo(f"Error validating system: {e}", err=True)








