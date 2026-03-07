"""
Scanning API routes.

Provides endpoints for triggering accessibility scans.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, require_role
from db.session import get_db
from models.evaluation import EvaluationProject
from models.page import Page
from models.user import User
from tasks.scan import scan_pages

router = APIRouter(tags=["Scanning"])


class ScanRequest(BaseModel):
    """Request schema for triggering a scan."""

    page_ids: Optional[list[str]] = None


class ScanResponse(BaseModel):
    """Response schema for scan trigger."""

    task_id: str
    status: str
    pages_queued: str


async def get_evaluation_for_user(
    evaluation_id: UUID,
    user: User,
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


@router.post(
    "/{evaluation_id}/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_scan(
    evaluation_id: UUID,
    request: ScanRequest = ScanRequest(),
    user: User = Depends(require_role("owner", "auditor")),
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    """
    Start an accessibility scan for an evaluation.

    Requires owner or auditor role.
    Triggers an async Celery task to run axe-core scans on pages.

    Args:
        evaluation_id: The evaluation UUID
        request: Optional list of specific page IDs to scan.
            If omitted, scans all pages.

    Returns:
        ScanResponse with task_id for polling

    Raises:
        404: Evaluation not found
        403: User doesn't have access or insufficient permissions
        400: Evaluation not in valid state for scanning
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Verify evaluation is in a valid state for scanning
    valid_states = ("SAMPLING", "AUDITING", "REPORTING")
    if evaluation.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation must be in SAMPLING or AUDITING status to start a scan. "
                   f"Current status: {evaluation.status}. "
                   f"Please run website exploration first.",
        )

    # Determine pages to queue
    page_ids = request.page_ids
    pages_queued_str = "all"

    if page_ids:
        # Validate page IDs exist
        for pid in page_ids:
            try:
                UUID(pid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid page ID format: {pid}",
                )
        pages_queued_str = str(len(page_ids))
    else:
        # Count pages for the response
        count_stmt = select(Page).where(Page.evaluation_id == evaluation_id)
        count_result = await db.execute(count_stmt)
        page_count = len(count_result.scalars().all())
        pages_queued_str = f"all ({page_count} pages)"

    # Dispatch Celery task
    task = scan_pages.apply_async(
        args=[str(evaluation_id)],
        kwargs={"page_ids": page_ids},
        queue="scan",
    )

    return ScanResponse(
        task_id=task.id,
        status="QUEUED",
        pages_queued=pages_queued_str,
    )
