"""
Reports API routes.

Provides endpoints for generating and downloading accessibility reports.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.logging import get_logger
from db.session import get_db
from models.evaluation import EvaluationProject
from models.user import User
from tasks.report import generate_pdf_report

logger = get_logger(__name__)

router = APIRouter(tags=["Reports"])


class ReportGenerationResponse(BaseModel):
    """Response for report generation request."""

    task_id: str
    status: str
    message: str


@router.post(
    "/{evaluation_id}/reports/generate",
    response_model=ReportGenerationResponse,
)
async def generate_report(
    evaluation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportGenerationResponse:
    """
    Start report generation for an evaluation.

    Triggers async report generation task and updates evaluation status to REPORTING.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        Task ID for tracking report generation progress
    """
    # Fetch evaluation
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

    # Check evaluation is in a valid state for report generation
    valid_states = ("SAMPLING", "AUDITING", "REPORTING", "COMPLETE")
    if evaluation.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate report for evaluation in {evaluation.status} status. Must be one of: {', '.join(valid_states)}",
        )

    # Update status to REPORTING
    if evaluation.status != "REPORTING":
        evaluation.status = "REPORTING"
        await db.flush()

    # Start async task
    task = generate_pdf_report.delay(str(evaluation_id))

    logger.info(
        "report_generation_started",
        evaluation_id=str(evaluation_id),
        task_id=task.id,
        user_id=str(user.id),
    )

    return ReportGenerationResponse(
        task_id=task.id,
        status="started",
        message="Report generation has been started. Check task status for progress.",
    )
