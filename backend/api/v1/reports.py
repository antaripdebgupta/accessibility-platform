"""
Reports API routes.

Provides endpoints for generating and downloading accessibility reports.
Supports PDF, EARL JSON-LD, and CSV export formats.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthenticatedUser, require_permission
from core.config import settings
from core.logging import get_logger
from db.session import get_db
from models.evaluation import EvaluationProject
from models.report import Report
from schemas.report import (
    ReportCreate,
    ReportGenerateResponse,
    ReportListResponse,
    ReportResponse,
)
from storage.operations import get_presigned_url
from tasks.report import generate_report

logger = get_logger(__name__)

router = APIRouter(tags=["Reports"])


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


def build_report_response(report: Report, include_download_url: bool = True) -> ReportResponse:
    """
    Build a ReportResponse from a Report model.

    Args:
        report: The Report ORM object
        include_download_url: Whether to generate presigned download URL

    Returns:
        ReportResponse schema object
    """
    download_url = None
    if include_download_url and report.storage_key:
        download_url = get_presigned_url(
            bucket=settings.minio_bucket_reports,
            key=report.storage_key,
            expires_hours=24,
        )

    return ReportResponse(
        id=report.id,
        evaluation_id=report.evaluation_id,
        report_type=report.report_type,
        conformance_verdict=report.conformance_verdict,
        criteria_passed=report.criteria_passed,
        criteria_failed=report.criteria_failed,
        criteria_na=report.criteria_na,
        total_findings=report.total_findings,
        storage_key=report.storage_key,
        download_url=download_url,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
    )


@router.post(
    "/{evaluation_id}/report",
    response_model=ReportGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_report(
    evaluation_id: UUID,
    body: Optional[ReportCreate] = None,
    user: AuthenticatedUser = Depends(require_permission("report.generate")),
    db: AsyncSession = Depends(get_db),
) -> ReportGenerateResponse:
    """
    Start report generation for an evaluation.

    Triggers async report generation task that creates PDF, EARL, and CSV reports.

    Args:
        evaluation_id: The evaluation UUID
        body: Optional report creation options

    Returns:
        Task ID for tracking report generation progress
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Check evaluation is in a valid state for report generation
    # AUDITING = scan complete, findings ready for review
    # REPORTING = report generation in progress
    # COMPLETE = report already generated (can regenerate)
    valid_states = ("AUDITING", "REPORTING", "COMPLETE")
    if evaluation.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation must be in AUDITING, REPORTING, or COMPLETE status to generate a report. "
                   f"Current status: {evaluation.status}. Complete the scan and review findings first.",
        )

    # Parse options from body
    report_types = ["full", "earl", "csv"]
    include_dismissed = False

    if body:
        if body.report_types:
            # Validate report types
            valid_types = {"full", "earl", "csv", "executive"}
            for rt in body.report_types:
                if rt not in valid_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid report type: {rt}. Valid types are: {', '.join(valid_types)}",
                    )
            report_types = body.report_types
        include_dismissed = body.include_dismissed

    # Start async task
    task = generate_report.apply_async(
        args=[str(evaluation_id)],
        kwargs={
            "report_types": report_types,
            "include_dismissed": include_dismissed,
        },
        queue="report",
    )

    logger.info(
        "report_generation_queued",
        evaluation_id=str(evaluation_id),
        task_id=task.id,
        user_id=str(user.id),
        report_types=report_types,
    )

    return ReportGenerateResponse(
        task_id=task.id,
        status="QUEUED",
        report_types=report_types,
    )


@router.get(
    "/{evaluation_id}/reports",
    response_model=ReportListResponse,
)
async def list_reports(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("report.read")),
    db: AsyncSession = Depends(get_db),
) -> ReportListResponse:
    """
    List all reports for an evaluation.

    Returns reports ordered by generation date (newest first).
    Each report includes a presigned download URL valid for 24 hours.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        List of reports with download URLs
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Fetch all reports for this evaluation
    stmt = (
        select(Report)
        .where(Report.evaluation_id == evaluation_id)
        .order_by(Report.generated_at.desc())
    )
    result = await db.execute(stmt)
    reports = result.scalars().all()

    # Build response with presigned URLs
    report_responses = [
        build_report_response(report, include_download_url=True)
        for report in reports
    ]

    return ReportListResponse(
        items=report_responses,
        total=len(report_responses),
    )


@router.get(
    "/{evaluation_id}/reports/latest",
    response_model=ReportResponse,
)
async def get_latest_report(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("report.read")),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    Get the most recent full report for an evaluation.

    Returns the latest PDF report with a presigned download URL.
    Returns 404 if no reports exist.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        The latest full report with download URL
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Fetch the most recent "full" type report
    stmt = (
        select(Report)
        .where(
            Report.evaluation_id == evaluation_id,
            Report.report_type == "full",
        )
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports found for this evaluation. Generate a report first.",
        )

    return build_report_response(report, include_download_url=True)
