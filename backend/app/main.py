"""
Sheet to Solfa - FastAPI Application.

Main entry point for the backend API server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import upload, jobs, export

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name}")
    settings.ensure_directories()
    logger.info(f"Storage directories initialized")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Convert PDF sheet music to tonic solfa notation",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if "*" in cors_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(export.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get(f"{settings.api_prefix}/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "endpoints": {
            "upload": f"{settings.api_prefix}/upload",
            "jobs": f"{settings.api_prefix}/jobs/{{job_id}}",
            "export": f"{settings.api_prefix}/export/{{job_id}}/{{format}}",
        },
        "supported_formats": ["txt", "json", "pdf"],
    }

