"""
Factories for dependency injection in entry points.

This module provides factories for creating use cases and adapters
with proper dependency injection.
"""

import logging
from pathlib import Path

from ..adapters.auto_updater import GitAutoUpdaterAdapter
from ..adapters.storage import JsonConfigStorageAdapter
from ..adapters.telegram import TelegramAdapter
from ..domain.ports import (
    AutoUpdaterPort,
    ConfigStoragePort,
    TelegramPort,
)
from ..usecases import (
    BotManagementUseCase,
    ConversationUseCase,
    SystemUseCase,
)


class UseCaseFactory:
    """Factory for creating use cases with dependencies."""

    def __init__(self, config_path: Path | None = None):
        """Initialize factory with configuration path."""
        self.config_path = config_path or Path("config")
        self._telegram_port: TelegramPort | None = None
        self._storage_port: ConfigStoragePort | None = None
        self._updater_port: AutoUpdaterPort | None = None

    def _get_telegram_port(self) -> TelegramPort:
        """Get or create Telegram port."""
        if self._telegram_port is None:
            self._telegram_port = TelegramAdapter()
        return self._telegram_port

    def _get_storage_port(self) -> ConfigStoragePort:
        """Get or create storage port."""
        if self._storage_port is None:
            self._storage_port = JsonConfigStorageAdapter(self.config_path)
        return self._storage_port

    def _get_updater_port(self) -> AutoUpdaterPort:
        """Get or create auto updater port."""
        if self._updater_port is None:
            self._updater_port = GitAutoUpdaterAdapter()
        return self._updater_port

    def create_bot_management_usecase(self) -> BotManagementUseCase:
        """Create BotManagementUseCase with dependencies."""
        return BotManagementUseCase(
            telegram_port=self._get_telegram_port(),
            storage_port=self._get_storage_port(),
        )

    def create_conversation_usecase(self) -> ConversationUseCase:
        """Create ConversationUseCase with dependencies."""
        return ConversationUseCase(
            storage_port=self._get_storage_port(),
        )

    def create_system_usecase(self) -> SystemUseCase:
        """Create SystemUseCase with dependencies."""
        return SystemUseCase(
            storage_port=self._get_storage_port(),
            updater_port=self._get_updater_port(),
        )


class EntryPointFactory:
    """Factory for creating entry points."""

    def __init__(self, config_path: Path | None = None):
        """Initialize factory with configuration path."""
        self.use_case_factory = UseCaseFactory(config_path)
        self.logger = logging.getLogger(__name__)

    def create_web_app(self):
        """Create Flask web application."""
        from .web import FlaskApp
        return FlaskApp(
            bot_usecase=self.use_case_factory.create_bot_management_usecase(),
            conversation_usecase=self.use_case_factory.create_conversation_usecase(),
            system_usecase=self.use_case_factory.create_system_usecase(),
        )

    def create_cli_app(self):
        """Create CLI application."""
        from .cli import CLIApp
        return CLIApp(
            bot_usecase=self.use_case_factory.create_bot_management_usecase(),
            conversation_usecase=self.use_case_factory.create_conversation_usecase(),
            system_usecase=self.use_case_factory.create_system_usecase(),
        )

    def create_api_app(self):
        """Create FastAPI application."""
        from .api import APIApp
        return APIApp(
            bot_usecase=self.use_case_factory.create_bot_management_usecase(),
            conversation_usecase=self.use_case_factory.create_conversation_usecase(),
            system_usecase=self.use_case_factory.create_system_usecase(),
        )










