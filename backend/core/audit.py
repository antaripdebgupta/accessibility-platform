"""
Audit logging service.

Provides a robust audit trail for all significant actions in the system.
Audit logging is designed to NEVER crash the main request — all exceptions
are caught and logged.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog


logger = logging.getLogger(__name__)


class AuditAction:
    """Pre-defined action constants for audit logging."""

    # Evaluation actions
    EVALUATION_CREATED = "evaluation.created"
    EVALUATION_UPDATED = "evaluation.updated"
    EVALUATION_DELETED = "evaluation.deleted"
    EVALUATION_ADVANCED = "evaluation.advanced"

    # Finding actions
    FINDING_CONFIRMED = "finding.confirmed"
    FINDING_DISMISSED = "finding.dismissed"
    FINDING_REOPENED = "finding.reopened"
    FINDING_CREATED = "finding.created"
    FINDING_UPDATED = "finding.updated"

    # Scan and crawl actions
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    CRAWL_STARTED = "crawl.started"
    CRAWL_COMPLETED = "crawl.completed"

    # Report actions
    REPORT_GENERATED = "report.generated"
    REPORT_DOWNLOADED = "report.downloaded"


def _convert_uuids_to_strings(data: Optional[dict]) -> Optional[dict]:
    """
    Recursively convert UUID values to strings for JSON serialization.

    Args:
        data: Dictionary that may contain UUID values

    Returns:
        New dictionary with all UUIDs converted to strings
    """
    if data is None:
        return None

    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _convert_uuids_to_strings(value)
        elif isinstance(value, list):
            result[key] = [
                str(item) if isinstance(item, UUID) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


async def log_action(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organisation_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Log an action to the audit trail.

    This function is designed to NEVER throw an exception. All errors are
    caught and logged, but the main request flow continues uninterrupted.

    Args:
        db: Async database session (the caller's transaction)
        action: Action identifier (use AuditAction constants)
        entity_type: Type of entity affected (finding, evaluation, page, report)
        entity_id: UUID of the affected entity (as string)
        user_id: UUID of the user who performed the action (as string)
        organisation_id: UUID of the organisation context (as string)
        before_state: Relevant fields before the change
        after_state: Relevant fields after the change
        ip_address: Client IP address

    Note:
        This function does NOT commit the transaction. The audit log row
        will be committed as part of the caller's session commit.
    """
    try:
        # Convert UUIDs in state dictionaries to strings
        safe_before_state = _convert_uuids_to_strings(before_state)
        safe_after_state = _convert_uuids_to_strings(after_state)

        # Convert string IDs to UUID objects for the database
        entity_uuid = UUID(entity_id) if entity_id else None
        user_uuid = UUID(user_id) if user_id else None
        org_uuid = UUID(organisation_id) if organisation_id else None

        audit_log = AuditLog(
            user_id=user_uuid,
            organisation_id=org_uuid,
            action=action,
            entity_type=entity_type,
            entity_id=entity_uuid,
            before_state=safe_before_state,
            after_state=safe_after_state,
            ip_address=ip_address,
        )

        db.add(audit_log)
        # NOTE: We do NOT flush or commit here — the caller's commit includes this

    except Exception as e:
        # Audit logging must NEVER crash the main request
        logger.error(
            f"Failed to create audit log entry: {e}",
            extra={
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "error": str(e),
            },
            exc_info=True,
        )
