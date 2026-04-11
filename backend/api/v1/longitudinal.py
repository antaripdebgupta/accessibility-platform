"""
Longitudinal API routes.

Provides endpoints for evaluation series and trend analysis:
- Series listing and detail
- Trend computation and analysis
- Evaluation registration in series
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user, require_permission, AuthenticatedUser
from core.logging import get_logger
from db.session import get_db
from models.evaluation import EvaluationProject
from models.evaluation_series import EvaluationSeries
from models.series_snapshot import SeriesSnapshot
from models.wcag import WcagCriterion
from longitudinal.series import (
    get_or_create_series,
    register_evaluation_in_series,
    update_snapshot,
)
from longitudinal.trends import (
    compute_trends,
    filter_trends_by_criterion,
    trend_report_to_dict,
)

logger = get_logger(__name__)
router = APIRouter(tags=["Longitudinal"])


# ----- Pydantic Schemas -----

class SeriesListItem(BaseModel):
    """Summary item for series list response."""
    id: str
    display_name: str
    target_url: str
    evaluation_count: int
    latest_verdict: Optional[str] = None
    latest_snapshot_date: Optional[str] = None
    overall_direction: str = "stable"  # "improving" | "regressing" | "stable"


class SeriesListResponse(BaseModel):
    """Response for GET /series endpoint."""
    items: list[SeriesListItem]
    total: int


class SnapshotResponse(BaseModel):
    """Response item for a snapshot."""
    id: str
    evaluation_id: str
    snapshot_date: str
    total_findings: int
    confirmed_findings: int
    dismissed_findings: int
    open_findings: int
    criteria_failed: int
    criteria_passed: int
    conformance_verdict: Optional[str] = None
    findings_by_severity: Optional[dict] = None
    findings_by_criterion: Optional[dict] = None


class SeriesDetailResponse(BaseModel):
    """Response for GET /series/{id} endpoint."""
    id: str
    display_name: str
    target_url: str
    organisation_id: str
    created_at: str
    updated_at: str
    snapshots: list[SnapshotResponse]


class EvaluationSeriesResponse(BaseModel):
    """Response for GET /evaluations/{id}/series endpoint."""
    series_id: str
    display_name: str
    target_url: str
    evaluation_count: int


class SeriesUpdateRequest(BaseModel):
    """Request body for PATCH /series/{id}."""
    display_name: str = Field(..., min_length=1, max_length=200)


class SnapshotCreatedResponse(BaseModel):
    """Response for POST /evaluations/{id}/series/register."""
    id: str
    series_id: str
    evaluation_id: str
    snapshot_date: str
    confirmed_findings: int
    criteria_failed: int


# ----- Helper Functions -----

async def _get_wcag_map(db: AsyncSession) -> dict[str, dict[str, str]]:
    """
    Build a mapping of criterion_id -> {name, level} from the database.
    """
    stmt = select(WcagCriterion)
    result = await db.execute(stmt)
    criteria = result.scalars().all()

    return {
        c.criterion_id: {"name": c.name, "level": c.level}
        for c in criteria
    }


async def _get_user_org_ids(user: AuthenticatedUser) -> list[UUID]:
    """Get list of organisation IDs the user belongs to."""
    return [role.organisation_id for role in user.organisation_roles]


async def _compute_overall_direction(snapshots: list[SeriesSnapshot]) -> str:
    """
    Compute overall direction from first to latest snapshot.
    """
    if len(snapshots) < 2:
        return "stable"

    sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
    first_confirmed = sorted_snapshots[0].confirmed_findings
    latest_confirmed = sorted_snapshots[-1].confirmed_findings

    if latest_confirmed < first_confirmed:
        return "improving"
    elif latest_confirmed > first_confirmed:
        return "regressing"
    else:
        return "stable"


# API Routes

@router.get(
    "/series",
    response_model=SeriesListResponse,
)
async def list_series(
    user: AuthenticatedUser = Depends(require_permission("evaluation.read")),
    db: AsyncSession = Depends(get_db),
) -> SeriesListResponse:
    """
    List all evaluation series for the current organisation.

    Returns series with evaluation count, latest verdict, and overall direction.
    """
    org_ids = await _get_user_org_ids(user)

    if not org_ids:
        return SeriesListResponse(items=[], total=0)

    # Fetch series with snapshots eagerly loaded
    stmt = (
        select(EvaluationSeries)
        .options(selectinload(EvaluationSeries.snapshots))
        .where(EvaluationSeries.organisation_id.in_(org_ids))
        .order_by(EvaluationSeries.updated_at.desc())
    )
    result = await db.execute(stmt)
    series_list = result.scalars().all()

    items = []
    for series in series_list:
        snapshots = list(series.snapshots)
        evaluation_count = len(snapshots)

        # Get latest snapshot data
        latest_verdict = None
        latest_snapshot_date = None
        if snapshots:
            sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date, reverse=True)
            latest = sorted_snapshots[0]
            latest_verdict = latest.conformance_verdict
            latest_snapshot_date = latest.snapshot_date.isoformat()

        # Compute overall direction
        overall_direction = await _compute_overall_direction(snapshots)

        items.append(SeriesListItem(
            id=str(series.id),
            display_name=series.display_name,
            target_url=series.target_url,
            evaluation_count=evaluation_count,
            latest_verdict=latest_verdict,
            latest_snapshot_date=latest_snapshot_date,
            overall_direction=overall_direction,
        ))

    return SeriesListResponse(items=items, total=len(items))


@router.get(
    "/series/{series_id}",
    response_model=SeriesDetailResponse,
)
async def get_series(
    series_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("evaluation.read")),
    db: AsyncSession = Depends(get_db),
) -> SeriesDetailResponse:
    """
    Get detailed information about a series including all snapshots.
    """
    org_ids = await _get_user_org_ids(user)

    # Fetch series with snapshots
    stmt = (
        select(EvaluationSeries)
        .options(selectinload(EvaluationSeries.snapshots))
        .where(
            and_(
                EvaluationSeries.id == series_id,
                EvaluationSeries.organisation_id.in_(org_ids),
            )
        )
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()

    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Series not found",
        )

    # Build snapshot responses ordered by date
    sorted_snapshots = sorted(series.snapshots, key=lambda s: s.snapshot_date)
    snapshots_data = [
        SnapshotResponse(
            id=str(s.id),
            evaluation_id=str(s.evaluation_id),
            snapshot_date=s.snapshot_date.isoformat(),
            total_findings=s.total_findings,
            confirmed_findings=s.confirmed_findings,
            dismissed_findings=s.dismissed_findings,
            open_findings=s.open_findings,
            criteria_failed=s.criteria_failed,
            criteria_passed=s.criteria_passed,
            conformance_verdict=s.conformance_verdict,
            findings_by_severity=s.findings_by_severity,
            findings_by_criterion=s.findings_by_criterion,
        )
        for s in sorted_snapshots
    ]

    return SeriesDetailResponse(
        id=str(series.id),
        display_name=series.display_name,
        target_url=series.target_url,
        organisation_id=str(series.organisation_id),
        created_at=series.created_at.isoformat(),
        updated_at=series.updated_at.isoformat(),
        snapshots=snapshots_data,
    )


@router.get(
    "/series/{series_id}/trends",
)
async def get_series_trends(
    series_id: UUID,
    last_n: Optional[int] = Query(
        None,
        ge=2,
        description="Only use last N snapshots for trend computation (minimum 2)",
    ),
    criterion: Optional[str] = Query(
        None,
        description="Return trend for a single criterion only",
    ),
    user: AuthenticatedUser = Depends(require_permission("evaluation.read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compute and return trend analysis for a series.

    Optional query params:
    - last_n: Only use last N snapshots (minimum 2)
    - criterion: Filter to a single WCAG criterion code
    """
    org_ids = await _get_user_org_ids(user)

    # Validate last_n parameter
    if last_n is not None and last_n < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="last_n must be at least 2",
        )

    # Fetch series with snapshots
    stmt = (
        select(EvaluationSeries)
        .options(selectinload(EvaluationSeries.snapshots))
        .where(
            and_(
                EvaluationSeries.id == series_id,
                EvaluationSeries.organisation_id.in_(org_ids),
            )
        )
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()

    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Series not found",
        )

    # Sort and optionally limit snapshots
    sorted_snapshots = sorted(series.snapshots, key=lambda s: s.snapshot_date)

    if last_n is not None and len(sorted_snapshots) > last_n:
        sorted_snapshots = sorted_snapshots[-last_n:]

    # Get WCAG criteria map
    wcag_map = await _get_wcag_map(db)

    # Compute trends
    trend_report = compute_trends(
        snapshots=sorted_snapshots,
        wcag_map=wcag_map,
        series_id=str(series.id),
        series_name=series.display_name,
        target_url=series.target_url,
    )

    # Filter by criterion if requested
    if criterion:
        trend_report = filter_trends_by_criterion(trend_report, criterion)

    return trend_report_to_dict(trend_report)


@router.get(
    "/evaluations/{evaluation_id}/series",
    response_model=EvaluationSeriesResponse,
)
async def get_evaluation_series(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("evaluation.read")),
    db: AsyncSession = Depends(get_db),
) -> EvaluationSeriesResponse:
    """
    Get the series that an evaluation belongs to.

    Returns 404 if the evaluation is not yet registered in a series.
    """
    org_ids = await _get_user_org_ids(user)

    # Check evaluation exists and user has access
    eval_stmt = select(EvaluationProject).where(
        and_(
            EvaluationProject.id == evaluation_id,
            EvaluationProject.organisation_id.in_(org_ids),
            EvaluationProject.status != "DELETED",
        )
    )
    eval_result = await db.execute(eval_stmt)
    evaluation = eval_result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Find snapshot for this evaluation
    snapshot_stmt = (
        select(SeriesSnapshot)
        .options(selectinload(SeriesSnapshot.series).selectinload(EvaluationSeries.snapshots))
        .where(SeriesSnapshot.evaluation_id == evaluation_id)
    )
    snapshot_result = await db.execute(snapshot_stmt)
    snapshot = snapshot_result.scalar_one_or_none()

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not yet registered in a series",
        )

    series = snapshot.series
    evaluation_count = len(series.snapshots)

    return EvaluationSeriesResponse(
        series_id=str(series.id),
        display_name=series.display_name,
        target_url=series.target_url,
        evaluation_count=evaluation_count,
    )


@router.post(
    "/evaluations/{evaluation_id}/series/register",
    response_model=SnapshotCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_evaluation_in_series_route(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("evaluation.advance")),
    db: AsyncSession = Depends(get_db),
) -> SnapshotCreatedResponse:
    """
    Manually register an evaluation in the longitudinal tracking series.

    Idempotent: returns existing snapshot if already registered.
    """
    org_ids = await _get_user_org_ids(user)

    # Check evaluation exists and user has access
    eval_stmt = select(EvaluationProject).where(
        and_(
            EvaluationProject.id == evaluation_id,
            EvaluationProject.organisation_id.in_(org_ids),
            EvaluationProject.status != "DELETED",
        )
    )
    eval_result = await db.execute(eval_stmt)
    evaluation = eval_result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Register in series
    snapshot = await register_evaluation_in_series(db, evaluation_id)

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register evaluation in series",
        )

    await db.commit()

    logger.info(
        "evaluation_registered_in_series",
        evaluation_id=str(evaluation_id),
        series_id=str(snapshot.series_id),
        snapshot_id=str(snapshot.id),
    )

    return SnapshotCreatedResponse(
        id=str(snapshot.id),
        series_id=str(snapshot.series_id),
        evaluation_id=str(snapshot.evaluation_id),
        snapshot_date=snapshot.snapshot_date.isoformat(),
        confirmed_findings=snapshot.confirmed_findings,
        criteria_failed=snapshot.criteria_failed,
    )


@router.patch(
    "/series/{series_id}",
    response_model=SeriesDetailResponse,
)
async def update_series(
    series_id: UUID,
    data: SeriesUpdateRequest,
    user: AuthenticatedUser = Depends(require_permission("org.manage_members")),
    db: AsyncSession = Depends(get_db),
) -> SeriesDetailResponse:
    """
    Update a series display name.

    Requires org owner role.
    """
    org_ids = await _get_user_org_ids(user)

    # Fetch series
    stmt = (
        select(EvaluationSeries)
        .options(selectinload(EvaluationSeries.snapshots))
        .where(
            and_(
                EvaluationSeries.id == series_id,
                EvaluationSeries.organisation_id.in_(org_ids),
            )
        )
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()

    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Series not found",
        )

    # Update display name
    series.display_name = data.display_name
    await db.commit()

    logger.info(
        "series_updated",
        series_id=str(series_id),
        display_name=data.display_name,
    )

    # Build response
    sorted_snapshots = sorted(series.snapshots, key=lambda s: s.snapshot_date)
    snapshots_data = [
        SnapshotResponse(
            id=str(s.id),
            evaluation_id=str(s.evaluation_id),
            snapshot_date=s.snapshot_date.isoformat(),
            total_findings=s.total_findings,
            confirmed_findings=s.confirmed_findings,
            dismissed_findings=s.dismissed_findings,
            open_findings=s.open_findings,
            criteria_failed=s.criteria_failed,
            criteria_passed=s.criteria_passed,
            conformance_verdict=s.conformance_verdict,
            findings_by_severity=s.findings_by_severity,
            findings_by_criterion=s.findings_by_criterion,
        )
        for s in sorted_snapshots
    ]

    return SeriesDetailResponse(
        id=str(series.id),
        display_name=series.display_name,
        target_url=series.target_url,
        organisation_id=str(series.organisation_id),
        created_at=series.created_at.isoformat(),
        updated_at=series.updated_at.isoformat(),
        snapshots=snapshots_data,
    )
