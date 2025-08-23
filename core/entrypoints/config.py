"""
Configuration for entry points.

This module provides configuration management for different environments.
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WebConfig:
    """Configuration for web entry point."""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "your-secret-key-here"
    session_timeout: int = 3600  # 1 hour


@dataclass
class APIConfig:
    """Configuration for API entry point."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = None
    api_key_header: str = "X-API-Key"
    rate_limit: int = 100  # requests per minute


@dataclass
class CLIConfig:
    """Configuration for CLI entry point."""
    verbose: bool = False
    config_file: Path | None = None
    log_level: str = "INFO"


@dataclass
class EntryPointConfig:
    """Main configuration for all entry points."""
    web: WebConfig = None
    api: APIConfig = None
    cli: CLIConfig = None
    config_path: Path = None

    def __post_init__(self):
        """Initialize default values."""
        if self.web is None:
            self.web = WebConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.cli is None:
            self.cli = CLIConfig()
        if self.config_path is None:
            self.config_path = Path("config")

        # Set CORS origins if not provided
        if self.api.cors_origins is None:
            self.api.cors_origins = ["http://localhost:3000", "http://localhost:5000"]


def load_config_from_env() -> EntryPointConfig:
    """Load configuration from environment variables."""
    config = EntryPointConfig()

    # Web configuration
    config.web.host = os.getenv("WEB_HOST", config.web.host)
    config.web.port = int(os.getenv("WEB_PORT", str(config.web.port)))
    config.web.debug = os.getenv("WEB_DEBUG", "false").lower() == "true"
    config.web.secret_key = os.getenv("WEB_SECRET_KEY", config.web.secret_key)
    config.web.session_timeout = int(os.getenv("WEB_SESSION_TIMEOUT", str(config.web.session_timeout)))

    # API configuration
    config.api.host = os.getenv("API_HOST", config.api.host)
    config.api.port = int(os.getenv("API_PORT", str(config.api.port)))
    config.api.debug = os.getenv("API_DEBUG", "false").lower() == "true"
    config.api.api_key_header = os.getenv("API_KEY_HEADER", config.api.api_key_header)
    config.api.rate_limit = int(os.getenv("API_RATE_LIMIT", str(config.api.rate_limit)))

    # CORS origins
    cors_origins = os.getenv("API_CORS_ORIGINS")
    if cors_origins:
        config.api.cors_origins = [origin.strip() for origin in cors_origins.split(",")]

    # CLI configuration
    config.cli.verbose = os.getenv("CLI_VERBOSE", "false").lower() == "true"
    config.cli.log_level = os.getenv("CLI_LOG_LEVEL", config.cli.log_level)

    # Config path
    config_path = os.getenv("CONFIG_PATH")
    if config_path:
        config.config_path = Path(config_path)

    return config


def validate_config(config: EntryPointConfig) -> None:
    """Validate configuration values."""
    errors = []

    # Validate web config
    if not (1 <= config.web.port <= 65535):
        errors.append(f"Invalid web port: {config.web.port}")

    if len(config.web.secret_key) < 16:
        errors.append("Web secret key must be at least 16 characters long")

    # Validate API config
    if not (1 <= config.api.port <= 65535):
        errors.append(f"Invalid API port: {config.api.port}")

    if config.web.port == config.api.port:
        errors.append("Web and API ports cannot be the same")

    # Validate config path
    if not config.config_path.exists():
        errors.append(f"Config path does not exist: {config.config_path}")

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))


def get_config() -> EntryPointConfig:
    """Get validated configuration."""
    config = load_config_from_env()
    validate_config(config)
    return config










