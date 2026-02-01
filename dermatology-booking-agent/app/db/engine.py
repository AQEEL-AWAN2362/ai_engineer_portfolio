from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Synchronous engine for initialization and sync operations
# Use echo only in development
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Test connections before use
    max_overflow=10,
    pool_size=5,
)

# Async engine for FastAPI application
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    max_overflow=10,
    pool_size=5,
)

# Async session factory
async_session = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

def init_db():
    """Initialize database tables (synchronous)"""
    try:
        SQLModel.metadata.create_all(sync_engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

async def get_async_session():
    """Get async session for dependency injection"""
    async with async_session() as session:
        yield session
