"""
Synchronous Database Engine for Celery Tasks.

Provides a properly configured synchronous SQLAlchemy engine and session
for use in Celery workers. This module handles the conversion of async
database URLs to psycopg2-compatible sync URLs.

The key difference from the async engine is:
- Uses psycopg2 driver instead of asyncpg
- Converts ssl=require to sslmode=require (psycopg2 syntax)
- Removes unsupported connection parameters

Usage:
    from db.sync_engine import get_sync_session, sync_engine

    def my_celery_task():
        session = get_sync_session()
        try:
            # ... do database work ...
            session.commit()
        finally:
            session.close()
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


def get_sync_database_url() -> str:
    """
    Convert async DATABASE_URL to a psycopg2-compatible sync URL.

    Handles:
      - postgresql+asyncpg:// → postgresql+psycopg2://
      - ?ssl=require          → ?sslmode=require   (psycopg2 rejects 'ssl=')
      - Removes unsupported parameters like channel_binding

    Returns:
        A properly formatted sync database URL for psycopg2.
    """
    db_url = settings.database_url

    # 1. Swap driver from asyncpg to psycopg2
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    # 2. Parse & fix query-string params properly
    parsed = urlparse(db_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # parse_qs returns lists; flatten to single values
    flat = {k: v[0] for k, v in params.items()}

    # Convert ssl=require → sslmode=require (psycopg2 doesn't understand 'ssl')
    if "ssl" in flat:
        ssl_val = flat.pop("ssl")
        # Only map the "require" value; drop anything else (e.g. "false")
        if ssl_val == "require":
            flat["sslmode"] = "require"

    # Remove unsupported parameters
    flat.pop("channel_binding", None)

    new_query = urlencode(flat)
    fixed_url = urlunparse(parsed._replace(query=new_query))

    # Log with masked password for debugging
    masked_netloc = f"{parsed.username}:***@{parsed.hostname}"
    if parsed.port:
        masked_netloc += f":{parsed.port}"
    safe_parsed = parsed._replace(netloc=masked_netloc, query=new_query)
    logger.info("sync_db_url_built", driver="psycopg2", url=urlunparse(safe_parsed))

    return fixed_url


# Build engine once at module import time (Celery worker startup)
_SYNC_DB_URL = get_sync_database_url()

sync_engine = create_engine(
    _SYNC_DB_URL,
    pool_pre_ping=True,  # Verify connection is alive before using
    pool_size=5,          # Maximum connections in pool
    max_overflow=10,      # Extra connections allowed beyond pool_size
    pool_recycle=1800,    # Recycle connections after 30 minutes
    pool_timeout=30,      # Wait up to 30s for a connection
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_sync_session() -> Session:
    """
    Get a synchronous database session for Celery tasks.

    Returns:
        A new SQLAlchemy Session instance.

    Note:
        The caller is responsible for closing the session after use.
        Use try/finally or a context manager to ensure proper cleanup.
    """
    return SyncSessionLocal()
