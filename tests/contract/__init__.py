"""
Contract tests for port interfaces.

These tests verify that adapters correctly implement the port contracts.
They ensure that the core business logic can work with any implementation
that follows the interface contracts.
"""

from .test_storage_port import *
from .test_telegram_port import *
from .test_updater_port import *

__all__ = [
    "test_telegram_port_contract",
    "test_storage_port_contract",
    "test_updater_port_contract",
]

