"""
Chat Manager Module

Manages conversation history, message tracking, and conversation utilities
for the MediChat RAG chatbot application.

Classes:
    ChatMessage: Represents a single message in the conversation
    ChatManager: Manages chat history and conversation context
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils import get_logger

logger = get_logger(__name__)


class ChatMessage:
    """
    Represents a single message in the conversation.
    
    Stores message content, role, timestamp, and optional metadata
    for tracking sources and other relevant information.
    
    Attributes:
        role (str): Message sender - "user" or "assistant"
        content (str): Message text content
        timestamp (datetime): When message was created
        metadata (dict): Optional metadata (sources, tokens, etc.)
    """
    
    def __init__(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a chat message.
        
        Args:
            role (str): "user" or "assistant"
            content (str): Message text content
            metadata (dict, optional): Additional metadata. Defaults to {}.
        
        Raises:
            ValueError: If role is not "user" or "assistant"
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Role must be 'user' or 'assistant', got {role}")
        
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary format.
        
        Returns:
            Dict[str, Any]: Message with ISO formatted timestamp
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class ChatManager:
    """
    Manages conversation history and provides chat utilities.
    
    Handles message storage, history trimming, conversation tracking,
    and provides methods for accessing and exporting chat data.
    
    Attributes:
        messages (List[ChatMessage]): Messages in the conversation
        max_history (int): Maximum messages to keep (older ones deleted)
        conversation_id (str): Unique conversation identifier
    """
    
    def __init__(self, max_history: int = 20) -> None:
        """
        Initialize ChatManager.
        
        Args:
            max_history (int, optional): Max messages to retain. Defaults to 20.
                When exceeded, oldest messages are removed.
        """
        self.messages: List[ChatMessage] = []
        self.max_history = max_history
        self.conversation_id = self._generate_conversation_id()
    
    def add_user_message(self, content: str) -> ChatMessage:
        """
        Add a user message to chat history.
        
        Args:
            content (str): User's message content
        
        Returns:
            ChatMessage: The created message object
        
        Example:
            >>> manager = ChatManager()
            >>> msg = manager.add_user_message("What is diabetes?")
        """
        message = ChatMessage(role="user", content=content)
        self.messages.append(message)
        self._trim_history()
        logger.info(f"Added user message: {content[:50]}...")
        return message
    
    def add_assistant_message(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Add an assistant message to chat history.
        
        Args:
            content (str): Assistant's response
            metadata (dict, optional): Sources, tokens, or other data
        
        Returns:
            ChatMessage: The created message object
        
        Example:
            >>> manager = ChatManager()
            >>> msg = manager.add_assistant_message("Diabetes is...", {"sources": [...]})
        """
        message = ChatMessage(role="assistant", content=content, metadata=metadata)
        self.messages.append(message)
        self._trim_history()
        logger.info(f"Added assistant message: {content[:50]}...")
        return message
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get complete chat history as list of dictionaries.
        
        Returns:
            List[Dict[str, Any]]: All messages with timestamps and metadata
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_context_messages(self, num_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get recent messages formatted for LLM context.
        
        Returns simplified message format suitable for sending to LLM API.
        
        Args:
            num_messages (int, optional): Number of recent messages. Defaults to 10.
        
        Returns:
            List[Dict[str, str]]: Recent messages with only role and content
        
        Example:
            >>> messages = manager.get_context_messages(num_messages=5)
            >>> # Use with LLM API
        """
        recent = self.messages[-num_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]
    
    def clear_history(self) -> None:
        """
        Clear all messages and reset conversation ID.
        
        This creates a fresh conversation context.
        """
        self.messages = []
        self.conversation_id = self._generate_conversation_id()
        logger.info("Chat history cleared")
    
    def get_last_user_message(self) -> Optional[str]:
        """
        Get the most recent user message.
        
        Returns:
            str: Last user message content, or None if no user messages
        """
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the most recent assistant message.
        
        Returns:
            str: Last assistant message content, or None if no assistant messages
        """
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None
    
    def get_message_count(self) -> Dict[str, int]:
        """
        Get count of user and assistant messages.
        
        Returns:
            Dict[str, int]: Counts for "user" and "assistant" keys
        """
        user_count = sum(1 for msg in self.messages if msg.role == "user")
        assistant_count = sum(1 for msg in self.messages if msg.role == "assistant")
        return {"user": user_count, "assistant": assistant_count}
    
    def get_sources_from_history(self) -> List[str]:
        """
        Extract all document sources from assistant messages.
        
        Returns:
            List[str]: Unique document sources mentioned in responses
        """
        sources = set()
        for msg in self.messages:
            if msg.role == "assistant" and msg.metadata:
                source = msg.metadata.get("source")
                if source:
                    sources.add(source)
        return list(sources)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive conversation summary.
        
        Returns:
            Dict[str, Any]: Summary including ID, message counts, sources, duration
        """
        counts = self.get_message_count()
        return {
            "conversation_id": self.conversation_id,
            "message_count": len(self.messages),
            "user_messages": counts["user"],
            "assistant_messages": counts["assistant"],
            "sources": self.get_sources_from_history(),
            "duration": self._get_conversation_duration()
        }
    
    def export_history(self) -> str:
        """
        Export chat history as formatted text.
        
        Returns:
            str: Formatted chat history suitable for display or saving
        """
        lines = [f"Conversation ID: {self.conversation_id}\n"]
        for msg in self.messages:
            role = msg.role.upper()
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{timestamp}] {role}:\n{msg.content}\n")
        
        return "\n".join(lines)
    
    def _trim_history(self) -> None:
        """Keep only the most recent messages if limit exceeded."""
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
            logger.info(f"Trimmed history to {self.max_history} messages")
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID using timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _get_conversation_duration(self) -> Optional[str]:
        """
        Calculate conversation duration from first to last message.
        
        Returns:
            str: Duration in human-readable format (e.g., "5m 30s")
        """
        if not self.messages:
            return None
        
        start = self.messages[0].timestamp
        end = self.messages[-1].timestamp
        duration = end - start
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
