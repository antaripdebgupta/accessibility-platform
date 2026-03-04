from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from core.config import settings

# Create the async engine once at import time.
# pool_pre_ping=True reconnects if the DB drops the connection.
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,        # log all SQL in debug mode
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
