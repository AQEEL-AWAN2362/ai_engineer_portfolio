import asyncio
import platform
import selectors

# Fix for Windows ProactorEventLoop compatibility with psycopg - MUST be FIRST
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg
import uvicorn
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from app.api.routes import agent_routes
from app.core.config import settings

import logging

# Setup logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown"""
    logger.info("Application starting up...")
    
    # For now, skip LangGraph store initialization due to Windows event loop issues
    # The agent works fine with conversation history stored in memory
    app.state.store = None
    app.state.checkpointer = None
    
    logger.info("Application started (using in-memory conversation history)")
    
    yield
    
    logger.info("Application shutting down...")


app = FastAPI(
    title="Dermatology AI Agent API",
    description="AI-powered appointment booking agent for dermatology clinic",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for production
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8501",  # Streamlit default
    "127.0.0.1:8501",
]

# In production, use environment variable or specific domains
if not settings.DEBUG:
    allowed_origins = [
        "https://yourdomain.com",
        "https://app.yourdomain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_routes.router, prefix="/agent", tags=["Agent"])

@app.get("/")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "Dermatology AI Agent API"}

@app.get("/health")
async def health_check_detailed():
    """Detailed health check with database connectivity"""
    try:
        store = getattr(app.state, 'store', None)
        if store:
            db_status = "connected"
        else:
            db_status = "not_initialized"
        
        return {
            "status": "healthy",
            "database": db_status,
            "service": "Dermatology AI Agent API"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")



if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())