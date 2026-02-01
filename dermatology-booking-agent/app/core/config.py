from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Ollama Configuration
    OLLAMA_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "https://api.ollama.com"
    OLLAMA_MODEL: str = "deepseek-v3.1:671b-cloud"
    
    # Gmail Configuration for Email Notifications
    GMAIL_SENDER_EMAIL: Optional[str] = None  # Gmail account email to send from
    GMAIL_CREDENTIALS_FILE: Optional[str] = None  # Path to credentials.json from Google Cloud
    GMAIL_TOKEN_FILE: Optional[str] = "token.json"  # Where to store OAuth2 token
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_ENABLED: bool = False  # Optional caching
    
    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    def validate_on_init(self) -> None:
        """Validate critical settings on initialization"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.OLLAMA_API_KEY and "localhost" not in self.OLLAMA_BASE_URL:
            logger.warning("OLLAMA_API_KEY not set. Using local Ollama endpoint.")
        if not self.GMAIL_SENDER_EMAIL:
            logger.warning("GMAIL_SENDER_EMAIL not set. Email notifications will be disabled.")
        if not self.GMAIL_CREDENTIALS_FILE:
            logger.warning("GMAIL_CREDENTIALS_FILE not set. Please set up Gmail OAuth2 credentials.")
        logger.info(f"Using LLM: {self.OLLAMA_MODEL} from {self.OLLAMA_BASE_URL}")
        if self.GMAIL_SENDER_EMAIL:
            logger.info("Gmail service enabled for email confirmations")
            logger.info(f"Email sender: {self.GMAIL_SENDER_EMAIL}")

try:
    settings = Settings()
    settings.validate_on_init()
except Exception as e:
    logger.error(f"Configuration error: {e}")
    raise
