"""
Bot domain entity and related value objects.

This module contains the core Bot entity and related domain logic
that represents a Telegram bot in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class BotStatus(Enum):
    """Bot status enumeration."""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class BotConfig:
    """Bot configuration value object."""
    
    name: str
    telegram_token: str
    openai_api_key: str
    assistant_id: str
    group_context_limit: int = 15
    enable_ai_responses: bool = True
    enable_voice_responses: bool = False
    voice_model: str = "tts-1"
    voice_type: str = "alloy"
    
    def validate(self) -> list[str]:
        """Validate bot configuration and return list of errors."""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Bot name is required")
        
        if not self.telegram_token or not self.telegram_token.startswith("5"):
            errors.append("Invalid Telegram token format")
        
        if not self.openai_api_key or not self.openai_api_key.startswith("sk-"):
            errors.append("Invalid OpenAI API key format")
        
        if not self.assistant_id or not self.assistant_id.startswith("asst_"):
            errors.append("Invalid Assistant ID format")
        
        if self.group_context_limit < 0:
            errors.append("Group context limit must be non-negative")
        
        if self.voice_model not in ["tts-1", "tts-1-hd"]:
            errors.append("Invalid voice model")
        
        if self.voice_type not in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
            errors.append("Invalid voice type")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "telegram_token": self.telegram_token,
            "openai_api_key": self.openai_api_key,
            "assistant_id": self.assistant_id,
            "group_context_limit": self.group_context_limit,
            "enable_ai_responses": self.enable_ai_responses,
            "enable_voice_responses": self.enable_voice_responses,
            "voice_model": self.voice_model,
            "voice_type": self.voice_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotConfig":
        """Create configuration from dictionary."""
        return cls(
            name=data.get("name", ""),
            telegram_token=data.get("telegram_token", ""),
            openai_api_key=data.get("openai_api_key", ""),
            assistant_id=data.get("assistant_id", ""),
            group_context_limit=data.get("group_context_limit", 15),
            enable_ai_responses=data.get("enable_ai_responses", True),
            enable_voice_responses=data.get("enable_voice_responses", False),
            voice_model=data.get("voice_model", "tts-1"),
            voice_type=data.get("voice_type", "alloy"),
        )


@dataclass
class Bot:
    """Bot domain entity."""
    
    id: int
    config: BotConfig
    status: BotStatus = BotStatus.STOPPED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_error: Optional[str] = None
    message_count: int = 0
    voice_message_count: int = 0
    
    def start(self) -> None:
        """Start the bot."""
        if self.status == BotStatus.RUNNING:
            raise ValueError("Bot is already running")
        
        self.status = BotStatus.RUNNING
        self.updated_at = datetime.now()
        self.last_error = None
    
    def stop(self) -> None:
        """Stop the bot."""
        if self.status == BotStatus.STOPPED:
            raise ValueError("Bot is already stopped")
        
        self.status = BotStatus.STOPPED
        self.updated_at = datetime.now()
    
    def set_error(self, error: str) -> None:
        """Set bot error status."""
        self.status = BotStatus.ERROR
        self.last_error = error
        self.updated_at = datetime.now()
    
    def update_config(self, new_config: BotConfig) -> None:
        """Update bot configuration."""
        errors = new_config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        self.config = new_config
        self.updated_at = datetime.now()
    
    def increment_message_count(self) -> None:
        """Increment message counter."""
        self.message_count += 1
    
    def increment_voice_message_count(self) -> None:
        """Increment voice message counter."""
        self.voice_message_count += 1
    
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self.status == BotStatus.RUNNING
    
    def is_enabled(self) -> bool:
        """Check if bot is enabled (running and no errors)."""
        return self.status == BotStatus.RUNNING and not self.last_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bot to dictionary."""
        return {
            "id": self.id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_error": self.last_error,
            "message_count": self.message_count,
            "voice_message_count": self.voice_message_count,
        }
    
    @classmethod
    def from_dict(cls, bot_id: int, data: Dict[str, Any]) -> "Bot":
        """Create bot from dictionary."""
        config = BotConfig.from_dict(data.get("config", {}))
        
        return cls(
            id=bot_id,
            config=config,
            status=BotStatus(data.get("status", "stopped")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            last_error=data.get("last_error"),
            message_count=data.get("message_count", 0),
            voice_message_count=data.get("voice_message_count", 0),
        )








