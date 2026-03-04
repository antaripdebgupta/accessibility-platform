"""
Accessibility Evaluation Platform — FastAPI Application Entry Point

Startup order:
  1. Configure logging (structlog)
  2. Initialise Firebase Admin SDK
  3. Create FastAPI app with CORS + middleware
  4. Mount all API routes
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import configure_logging, get_logger
from core.firebase import init_firebase
from api.router import api_router

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once on startup, and once on shutdown."""
    # Startup
    logger.info(
        "app_starting",
        name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    init_firebase()
    logger.info("app_ready")

    yield  # Application is running

    # Shutdown
    logger.info("app_shutting_down")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="End-to-End Accessibility Evaluation Platform (WCAG-EM)",
    docs_url="/api/v1/docs",      # Swagger UI
    redoc_url="/api/v1/redoc",    # ReDoc
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routes
app.include_router(api_router)
