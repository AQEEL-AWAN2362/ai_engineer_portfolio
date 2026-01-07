"""
Utility functions for logging, formatting, and error handling
"""

import logging
import os
from typing import Any, Dict, List
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger with consistent formatting
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler
        fh = logging.FileHandler(os.path.join(log_dir, "medchat.log"))
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger


def format_response(content: str, sources: List[Dict[str, Any]]) -> str:
    """
    Format response with sources
    
    Args:
        content: Main response text
        sources: List of source documents
    
    Returns:
        Formatted response string
    """
    formatted = content
    
    if sources:
        formatted += "\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            filename = metadata.get("source", "Unknown")
            chunk_id = metadata.get("chunk_id", "Unknown")
            formatted += f"- {filename} (Chunk {chunk_id})\n"
    
    return formatted


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    
    Args:
        text: User input text
    
    Returns:
        Cleaned input
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove potentially harmful characters
    harmful_chars = ["<", ">", "{", "}", "[", "]", "\x00"]
    for char in harmful_chars:
        text = text.replace(char, "")
    
    return text.strip()


def format_token_count(count: int) -> str:
    """
    Format token count for display
    
    Args:
        count: Number of tokens
    
    Returns:
        Formatted string
    """
    if count < 1000:
        return f"{count} tokens"
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K tokens"
    else:
        return f"{count / 1_000_000:.1f}M tokens"


def get_timestamp() -> str:
    """Get current timestamp as formatted string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_document_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format document metadata for display
    
    Args:
        metadata: Document metadata dictionary
    
    Returns:
        Formatted metadata string
    """
    parts = []
    
    if "source" in metadata:
        parts.append(f"📄 {metadata['source']}")
    
    if "chunk_id" in metadata:
        parts.append(f"Chunk #{metadata['chunk_id']}")
    
    if "type" in metadata:
        parts.append(f"Type: {metadata['type']}")
    
    return " | ".join(parts) if parts else "No metadata"


def validate_pdf_file(filename: str) -> bool:
    """
    Validate if file is a PDF
    
    Args:
        filename: Filename to validate
    
    Returns:
        True if valid PDF
    """
    return filename.lower().endswith(".pdf")


def create_error_message(error: Exception, context: str = "") -> str:
    """
    Create user-friendly error message
    
    Args:
        error: Exception object
        context: Additional context about where error occurred
    
    Returns:
        User-friendly error message
    """
    error_msg = str(error)
    
    if context:
        return f"❌ Error {context}: {error_msg}"
    else:
        return f"❌ An error occurred: {error_msg}"


def split_into_chunks(text: str, chunk_size: int = 100) -> List[str]:
    """
    Simple text chunking utility
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks


def print_welcome_message() -> None:
    """Print welcome message to console"""
    print("""
    ╔════════════════════════════════════════╗
    ║     🏥 MediChat RAG - Welcome! 🏥      ║
    ║  Medical Knowledge Assistant with RAG  ║
    ╚════════════════════════════════════════╝
    """)


def print_section_header(title: str) -> None:
    """
    Print formatted section header
    
    Args:
        title: Section title
    """
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")


class TokenCounter:
    """Utility class for estimating token counts"""
    
    # Rough estimation: 1 token ≈ 4 characters
    CHARS_PER_TOKEN = 4
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to count
        
        Returns:
            Estimated token count
        """
        return len(text) // TokenCounter.CHARS_PER_TOKEN
    
    @staticmethod
    def estimate_from_documents(documents: List[Dict[str, Any]]) -> int:
        """
        Estimate total tokens from documents
        
        Args:
            documents: List of documents
        
        Returns:
            Total estimated tokens
        """
        total_chars = sum(
            len(doc.get("content", ""))
            for doc in documents
        )
        return total_chars // TokenCounter.CHARS_PER_TOKEN
