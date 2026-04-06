"""
Row-Level Security (RLS) utilities.

Provides functions to set PostgreSQL session variables for RLS policies.
These variables are used by RLS policies to filter data by organisation.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger

logger = get_logger(__name__)


async def set_rls_context(
    db: AsyncSession,
    user_id: str,
    organisation_id: str,
) -> None:
    """Set RLS context variables for the current database transaction.

    Uses SET LOCAL to scope variables to the current transaction only.
    This ensures RLS policies filter data to the specified organisation.

    IMPORTANT: These variables are used by PostgreSQL RLS policies. The policies
    use current_setting('app.current_org_id', true) to filter rows.

    Args:
        db: Async database session (must be within a transaction)
        user_id: Current user's UUID as string
        organisation_id: Current organisation's UUID as string
    """
    try:
        # SET LOCAL scopes the setting to the current transaction only
        # This is crucial for security - the setting is automatically
        # cleared when the transaction ends
        await db.execute(
            text(f"SET LOCAL app.current_user_id = '{user_id}'")
        )
        await db.execute(
            text(f"SET LOCAL app.current_org_id = '{organisation_id}'")
        )

        logger.debug(
            "rls_context_set",
            user_id=user_id,
            organisation_id=organisation_id,
        )
    except Exception as e:
        logger.error(
            "rls_context_set_failed",
            user_id=user_id,
            organisation_id=organisation_id,
            error=str(e),
        )
        raise


async def clear_rls_context(db: AsyncSession) -> None:
    """Clear RLS context variables.

    This is generally not needed because SET LOCAL is transaction-scoped,
    but can be used for explicit cleanup in tests or special cases.

    Args:
        db: Async database session
    """
    try:
        await db.execute(text("RESET app.current_user_id"))
        await db.execute(text("RESET app.current_org_id"))
        logger.debug("rls_context_cleared")
    except Exception as e:
        logger.warning(
            "rls_context_clear_failed",
            error=str(e),
        )
