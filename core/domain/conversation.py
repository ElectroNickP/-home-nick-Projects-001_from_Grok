"""
Conversation domain entity and related value objects.

This module contains the core Conversation entity and related domain logic
that represents a conversation between a user and a bot.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Message:
    """Message value object."""
    
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class ConversationKey:
    """Conversation key value object."""
    
    bot_id: int
    chat_id: str
    
    def __str__(self) -> str:
        """String representation of conversation key."""
        return f"{self.bot_id}:{self.chat_id}"
    
    @classmethod
    def from_string(cls, key_string: str) -> "ConversationKey":
        """Create conversation key from string."""
        try:
            bot_id_str, chat_id = key_string.split(":", 1)
            return cls(bot_id=int(bot_id_str), chat_id=chat_id)
        except (ValueError, IndexError):
            raise ValueError(f"Invalid conversation key format: {key_string}")


@dataclass
class Conversation:
    """Conversation domain entity."""
    
    key: ConversationKey
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.message_count += 1
        self.updated_at = datetime.now()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self.add_message("assistant", content)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages from the conversation."""
        return self.messages[-limit:] if self.messages else []
    
    def get_context_for_ai(self, limit: int = 15) -> List[Dict[str, str]]:
        """Get conversation context formatted for AI processing."""
        recent_messages = self.get_recent_messages(limit)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
    
    def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self.messages.clear()
        self.message_count = 0
        self.updated_at = datetime.now()
    
    def is_empty(self) -> bool:
        """Check if conversation is empty."""
        return len(self.messages) == 0
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def get_last_user_message(self) -> Optional[Message]:
        """Get the last user message in the conversation."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the last assistant message in the conversation."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "key": str(self.key),
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary."""
        key = ConversationKey.from_string(data["key"])
        messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]
        
        return cls(
            key=key,
            messages=messages,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data.get("message_count", len(messages)),
        )









