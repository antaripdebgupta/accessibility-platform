"""
Accessibility Evaluation Platform — FastAPI Application Entry Point

Startup order:
  1. Configure logging (structlog)
  2. Run database migrations (Alembic)
  3. Initialise Firebase Admin SDK
  4. Create FastAPI app with CORS + middleware
  5. Mount all API routes
"""

import subprocess
import sys
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


def run_migrations():
    """Run Alembic migrations on startup.

    This allows deployments on platforms without shell access (e.g., Render free tier).
    Migrations are idempotent — running them multiple times is safe.
    """
    import os

    # Log the database URL (masked) for debugging
    db_url = settings.database_url
    masked_url = db_url
    if "@" in db_url:
        # Mask password in URL for logging
        parts = db_url.split("@")
        prefix = parts[0]
        if ":" in prefix:
            scheme_user = prefix.rsplit(":", 1)[0]
            masked_url = f"{scheme_user}:***@{parts[1]}"

    logger.info("running_migrations",
                action="alembic upgrade head",
                database_url=masked_url,
                cwd=os.getcwd())
    try:
        # Ensure we run from the backend directory where alembic.ini lives
        app_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=120,  # Increased timeout for cold-start connections
            cwd=app_dir,
        )
        if result.returncode == 0:
            logger.info("migrations_completed", stdout=result.stdout.strip())
        else:
            logger.error(
                "migrations_failed",
                returncode=result.returncode,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
            )
            # Don't exit — the app might still work if tables exist
    except subprocess.TimeoutExpired:
        logger.error("migrations_timeout", message="Migration took longer than 120s")
    except Exception as e:
        logger.error("migrations_error", error=str(e), error_type=type(e).__name__)


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

    # Run database migrations (safe to run on every deploy)
    run_migrations()

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
