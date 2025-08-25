"""Main FastAPI application for TokenGovernor"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List, Optional

from ..core.config import settings
from ..database.connection import db_manager
from .routes import projects, tasks, status, tokens
from .middleware import token_tracking_middleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.logging.level.upper()),
    format=settings.logging.format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting TokenGovernor API")
    await db_manager.initialize()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TokenGovernor API")


# Create FastAPI app
app = FastAPI(
    title="TokenGovernor API",
    description="Governance system for agentic coding workflows",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add token tracking middleware
app.middleware("http")(token_tracking_middleware)

# Include routers
app.include_router(projects.router, prefix=f"{settings.api_prefix}/projects", tags=["projects"])
app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])
app.include_router(tokens.router, prefix=f"{settings.api_prefix}/tokens", tags=["tokens"])
app.include_router(status.router, prefix=f"{settings.api_prefix}/status", tags=["status"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TokenGovernor API",
        "version": "0.1.0",
        "phase": settings.current_phase,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        async with db_manager.get_connection() as db:
            await db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "phase": settings.current_phase
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "tokengovernor.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )