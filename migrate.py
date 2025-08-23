#!/usr/bin/env python3
"""
Migration CLI for Telegram Bot Manager.

This script provides a convenient command-line interface for migrating
from the old monolithic architecture to the new hexagonal architecture.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from migration.migrate_v1_to_v2 import main

if __name__ == "__main__":
    sys.exit(main())







