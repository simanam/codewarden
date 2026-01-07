"""CodeWarden API - Main Application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import (
    dashboard_router,
    events_router,
    projects_router,
    security_router,
    telemetry_router,
    webhooks_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting CodeWarden API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    logger.info("Shutting down CodeWarden API...")


app = FastAPI(
    title="CodeWarden API",
    description="Security and observability platform for solopreneurs",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://codewarden.io",
        "https://www.codewarden.io",
        "https://app.codewarden.io",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Requested-With"],
)

# Include routers
app.include_router(telemetry_router)  # /v1/telemetry, /v1/evidence, /v1/health
app.include_router(dashboard_router)  # /api/dashboard/* (for Next.js frontend)
app.include_router(security_router)   # /api/dashboard/security/* (security scanning)
app.include_router(webhooks_router)   # /webhooks/* (Telegram, GitHub, Stripe)
app.include_router(events_router)     # /api/v1/events (legacy)
app.include_router(projects_router)   # /api/v1/projects


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to CodeWarden API", "docs": "/docs"}
