"""
Audit Log API routes.

Provides endpoints for retrieving audit log entries for evaluations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import AuthenticatedUser, require_permission
from db.session import get_db
from models.audit_log import AuditLog
from models.evaluation import EvaluationProject
from models.finding import Finding

router = APIRouter(tags=["Audit"])


class AuditLogEntry(BaseModel):
    """Schema for an audit log entry."""

    id: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_label: Optional[str] = None  # Human-readable label for the entity
    user_email: Optional[str] = None
    display_name: Optional[str] = None
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response schema for audit log list."""

    items: list[AuditLogEntry]
    total: int


async def get_evaluation_for_user(
    evaluation_id: UUID,
    user: AuthenticatedUser,
    db: AsyncSession,
) -> EvaluationProject:
    """
    Fetch evaluation by ID and verify user has access.

    Raises 404 if not found, 403 if user doesn't have access.
    """
    stmt = select(EvaluationProject).where(
        EvaluationProject.id == evaluation_id,
        EvaluationProject.status != "DELETED",
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Check user has access to this evaluation's organisation
    user_org_ids = [role.organisation_id for role in user.organisation_roles]
    if evaluation.organisation_id not in user_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this evaluation",
        )

    return evaluation


@router.get(
    "/{evaluation_id}/audit-log",
    response_model=AuditLogResponse,
)
async def get_evaluation_audit_log(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("audit_log.read")),
    db: AsyncSession = Depends(get_db),
) -> AuditLogResponse:
    """
    Get audit log entries for an evaluation.

    Returns audit log entries for:
    - The evaluation itself (entity_type = 'evaluation', entity_id = evaluation_id)
    - All findings belonging to this evaluation
    - Scan and crawl events for this evaluation

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        AuditLogResponse with list of audit log entries

    Raises:
        404: Evaluation not found
        403: User doesn't have access
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Get all findings for this evaluation with criterion info for labels
    finding_stmt = (
        select(Finding)
        .options(selectinload(Finding.criterion))
        .where(Finding.evaluation_id == evaluation_id)
    )
    finding_result = await db.execute(finding_stmt)
    findings = finding_result.scalars().all()

    # Build a lookup map: finding_id -> human-readable label
    finding_labels = {}
    for f in findings:
        if f.criterion:
            label = f"{f.criterion.criterion_id}: {f.criterion.name}"
        elif f.description:
            label = f.description[:50] + ("..." if len(f.description) > 50 else "")
        else:
            label = f"Finding {str(f.id)[:8]}"
        finding_labels[f.id] = label

    finding_ids = list(finding_labels.keys())

    # Build query for audit logs
    # Match: evaluation itself, or any finding belonging to it
    conditions = [
        # Direct evaluation logs
        (AuditLog.entity_type == "evaluation") & (AuditLog.entity_id == evaluation_id),
        # Scan/crawl logs for this evaluation
        (AuditLog.entity_type == "scan") & (AuditLog.entity_id == evaluation_id),
        (AuditLog.entity_type == "crawl") & (AuditLog.entity_id == evaluation_id),
        # Report logs for this evaluation
        (AuditLog.entity_type == "report") & (AuditLog.entity_id == evaluation_id),
    ]

    # Add finding conditions if there are findings
    if finding_ids:
        conditions.append(
            (AuditLog.entity_type == "finding") & (AuditLog.entity_id.in_(finding_ids))
        )

    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(or_(*conditions))
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )

    result = await db.execute(stmt)
    audit_logs = result.scalars().all()

    # Build response
    items = []
    for log in audit_logs:
        # Determine the entity label based on entity type
        entity_label = None
        if log.entity_type == "finding" and log.entity_id:
            entity_label = finding_labels.get(log.entity_id)
        elif log.entity_type == "evaluation":
            entity_label = evaluation.title
        elif log.entity_type == "scan":
            entity_label = "Accessibility Scan"
        elif log.entity_type == "crawl":
            entity_label = "Site Crawl"
        elif log.entity_type == "report":
            entity_label = "Conformance Report"

        items.append(
            AuditLogEntry(
                id=str(log.id),
                action=log.action,
                entity_type=log.entity_type,
                entity_id=str(log.entity_id) if log.entity_id else None,
                entity_label=entity_label,
                user_email=log.user.email if log.user else None,
                display_name=log.user.display_name if log.user else None,
                before_state=log.before_state,
                after_state=log.after_state,
                created_at=log.created_at,
            )
        )

    return AuditLogResponse(items=items, total=len(items))
