"""
Series Management Service.

Provides functions for managing evaluation series:
- URL normalisation for consistent series matching
- Series creation and lookup
- Snapshot registration and updates
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.logging import get_logger
from models.evaluation import EvaluationProject
from models.evaluation_series import EvaluationSeries
from models.finding import Finding
from models.report import Report
from models.series_snapshot import SeriesSnapshot
from models.wcag import WcagCriterion

logger = get_logger(__name__)


def normalise_url(url: str) -> str:
    """
    Normalise a URL for consistent series matching.

    - Strips trailing slash
    - Lowercases scheme and host
    - Preserves path as-is (case-sensitive)

    Args:
        url: The URL to normalise

    Returns:
        Normalised URL string
    """
    if not url:
        return url

    parsed = urlparse(url)

    # Lowercase scheme and netloc (host:port)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Keep path as-is but strip trailing slash
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

    # Reconstruct URL without query/fragment for series matching
    normalised = urlunparse((scheme, netloc, path, "", "", ""))

    return normalised


async def get_or_create_series(
    db: AsyncSession,
    organisation_id: UUID,
    target_url: str,
    display_name: Optional[str] = None,
) -> EvaluationSeries:
    """
    Get or create an evaluation series for a target URL.

    Args:
        db: Async database session
        organisation_id: Organisation UUID
        target_url: Target website URL
        display_name: Human-readable label (defaults to hostname if not provided)

    Returns:
        EvaluationSeries instance (existing or newly created)
    """
    # Normalise URL for consistent matching
    normalised_url = normalise_url(target_url)

    # Try to find existing series
    stmt = select(EvaluationSeries).where(
        and_(
            EvaluationSeries.organisation_id == organisation_id,
            EvaluationSeries.target_url == normalised_url,
        )
    )
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()

    if series is not None:
        logger.debug(
            "series_found",
            series_id=str(series.id),
            target_url=normalised_url,
        )
        return series

    # Generate display name from hostname if not provided
    if display_name is None:
        parsed = urlparse(normalised_url)
        display_name = parsed.netloc or normalised_url[:50]

    # Create new series
    series = EvaluationSeries(
        organisation_id=organisation_id,
        target_url=normalised_url,
        display_name=display_name,
    )
    db.add(series)
    await db.flush()

    logger.info(
        "series_created",
        series_id=str(series.id),
        organisation_id=str(organisation_id),
        target_url=normalised_url,
        display_name=display_name,
    )

    return series


async def _compute_snapshot_metrics(
    db: AsyncSession,
    evaluation_id: UUID,
) -> dict:
    """
    Compute snapshot metrics from an evaluation's findings.

    Args:
        db: Async database session
        evaluation_id: Evaluation UUID

    Returns:
        Dict with all computed snapshot fields
    """
    # Get all findings for this evaluation with their criteria
    findings_stmt = (
        select(Finding)
        .options(selectinload(Finding.criterion))
        .where(Finding.evaluation_id == evaluation_id)
    )
    findings_result = await db.execute(findings_stmt)
    findings = list(findings_result.scalars().all())

    # Compute counts by status
    total_findings = len(findings)
    confirmed_findings = sum(1 for f in findings if f.status == "CONFIRMED")
    dismissed_findings = sum(1 for f in findings if f.status == "DISMISSED")
    open_findings = sum(1 for f in findings if f.status == "OPEN")

    # Compute findings by severity (confirmed only)
    findings_by_severity = defaultdict(int)
    for f in findings:
        if f.status == "CONFIRMED" and f.severity:
            findings_by_severity[f.severity] += 1

    # Compute findings by criterion (confirmed only)
    findings_by_criterion = defaultdict(int)
    criterion_ids_with_findings = set()
    for f in findings:
        if f.status == "CONFIRMED" and f.criterion:
            criterion_code = f.criterion.criterion_id
            findings_by_criterion[criterion_code] += 1
            criterion_ids_with_findings.add(f.criterion_id)

    # Count distinct criteria with confirmed findings
    criteria_failed = len(criterion_ids_with_findings)

    # Get latest report verdict
    report_stmt = (
        select(Report)
        .where(Report.evaluation_id == evaluation_id)
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    latest_report = report_result.scalar_one_or_none()

    conformance_verdict = None
    criteria_passed = 0
    if latest_report:
        conformance_verdict = latest_report.conformance_verdict
        criteria_passed = latest_report.criteria_passed or 0

    return {
        "total_findings": total_findings,
        "confirmed_findings": confirmed_findings,
        "dismissed_findings": dismissed_findings,
        "open_findings": open_findings,
        "criteria_failed": criteria_failed,
        "criteria_passed": criteria_passed,
        "conformance_verdict": conformance_verdict,
        "findings_by_severity": dict(findings_by_severity) if findings_by_severity else None,
        "findings_by_criterion": dict(findings_by_criterion) if findings_by_criterion else None,
    }


async def register_evaluation_in_series(
    db: AsyncSession,
    evaluation_id: UUID,
) -> Optional[SeriesSnapshot]:
    """
    Register an evaluation in its longitudinal series.

    Creates a snapshot capturing the evaluation's current metrics.
    Idempotent: returns existing snapshot if already registered.

    Args:
        db: Async database session
        evaluation_id: Evaluation UUID

    Returns:
        SeriesSnapshot instance or None if evaluation not found
    """
    # Fetch the evaluation
    eval_stmt = select(EvaluationProject).where(EvaluationProject.id == evaluation_id)
    eval_result = await db.execute(eval_stmt)
    evaluation = eval_result.scalar_one_or_none()

    if evaluation is None:
        logger.warning(
            "register_evaluation_not_found",
            evaluation_id=str(evaluation_id),
        )
        return None

    # Check if snapshot already exists for this evaluation
    existing_stmt = select(SeriesSnapshot).where(
        SeriesSnapshot.evaluation_id == evaluation_id
    )
    existing_result = await db.execute(existing_stmt)
    existing_snapshot = existing_result.scalar_one_or_none()

    if existing_snapshot is not None:
        logger.debug(
            "snapshot_already_exists",
            evaluation_id=str(evaluation_id),
            snapshot_id=str(existing_snapshot.id),
        )
        return existing_snapshot

    # Get or create the series
    series = await get_or_create_series(
        db=db,
        organisation_id=evaluation.organisation_id,
        target_url=evaluation.target_url,
    )

    # Compute metrics
    metrics = await _compute_snapshot_metrics(db, evaluation_id)

    # Create snapshot
    snapshot = SeriesSnapshot(
        series_id=series.id,
        evaluation_id=evaluation_id,
        snapshot_date=evaluation.created_at,
        total_findings=metrics["total_findings"],
        confirmed_findings=metrics["confirmed_findings"],
        dismissed_findings=metrics["dismissed_findings"],
        open_findings=metrics["open_findings"],
        criteria_failed=metrics["criteria_failed"],
        criteria_passed=metrics["criteria_passed"],
        conformance_verdict=metrics["conformance_verdict"],
        findings_by_severity=metrics["findings_by_severity"],
        findings_by_criterion=metrics["findings_by_criterion"],
    )
    db.add(snapshot)
    await db.flush()

    logger.info(
        "snapshot_created",
        snapshot_id=str(snapshot.id),
        series_id=str(series.id),
        evaluation_id=str(evaluation_id),
        confirmed_findings=metrics["confirmed_findings"],
        criteria_failed=metrics["criteria_failed"],
    )

    return snapshot


async def update_snapshot(
    db: AsyncSession,
    evaluation_id: UUID,
) -> Optional[SeriesSnapshot]:
    """
    Update or create a snapshot for an evaluation.

    Re-computes all metrics from the evaluation's current findings.
    Used when findings are confirmed/dismissed after initial snapshot creation.

    Args:
        db: Async database session
        evaluation_id: Evaluation UUID

    Returns:
        Updated or created SeriesSnapshot instance
    """
    # Check if snapshot exists
    existing_stmt = (
        select(SeriesSnapshot)
        .where(SeriesSnapshot.evaluation_id == evaluation_id)
    )
    existing_result = await db.execute(existing_stmt)
    existing_snapshot = existing_result.scalar_one_or_none()

    if existing_snapshot is None:
        # No existing snapshot - create one via register
        return await register_evaluation_in_series(db, evaluation_id)

    # Re-compute metrics
    metrics = await _compute_snapshot_metrics(db, evaluation_id)

    # Update existing snapshot
    existing_snapshot.total_findings = metrics["total_findings"]
    existing_snapshot.confirmed_findings = metrics["confirmed_findings"]
    existing_snapshot.dismissed_findings = metrics["dismissed_findings"]
    existing_snapshot.open_findings = metrics["open_findings"]
    existing_snapshot.criteria_failed = metrics["criteria_failed"]
    existing_snapshot.criteria_passed = metrics["criteria_passed"]
    existing_snapshot.conformance_verdict = metrics["conformance_verdict"]
    existing_snapshot.findings_by_severity = metrics["findings_by_severity"]
    existing_snapshot.findings_by_criterion = metrics["findings_by_criterion"]

    await db.flush()

    logger.info(
        "snapshot_updated",
        snapshot_id=str(existing_snapshot.id),
        evaluation_id=str(evaluation_id),
        confirmed_findings=metrics["confirmed_findings"],
        criteria_failed=metrics["criteria_failed"],
    )

    return existing_snapshot


# Synchronous versions for Celery tasks
def get_or_create_series_sync(
    session,
    organisation_id: UUID,
    target_url: str,
    display_name: Optional[str] = None,
) -> EvaluationSeries:
    """
    Synchronous version of get_or_create_series for Celery tasks.
    """
    normalised_url = normalise_url(target_url)

    stmt = select(EvaluationSeries).where(
        and_(
            EvaluationSeries.organisation_id == organisation_id,
            EvaluationSeries.target_url == normalised_url,
        )
    )
    result = session.execute(stmt)
    series = result.scalar_one_or_none()

    if series is not None:
        return series

    if display_name is None:
        parsed = urlparse(normalised_url)
        display_name = parsed.netloc or normalised_url[:50]

    series = EvaluationSeries(
        organisation_id=organisation_id,
        target_url=normalised_url,
        display_name=display_name,
    )
    session.add(series)
    session.flush()

    logger.info(
        "series_created_sync",
        series_id=str(series.id),
        target_url=normalised_url,
    )

    return series


def _compute_snapshot_metrics_sync(session, evaluation_id: UUID) -> dict:
    """
    Synchronous version of _compute_snapshot_metrics for Celery tasks.
    """
    findings_stmt = (
        select(Finding)
        .options(selectinload(Finding.criterion))
        .where(Finding.evaluation_id == evaluation_id)
    )
    findings_result = session.execute(findings_stmt)
    findings = list(findings_result.scalars().all())

    total_findings = len(findings)
    confirmed_findings = sum(1 for f in findings if f.status == "CONFIRMED")
    dismissed_findings = sum(1 for f in findings if f.status == "DISMISSED")
    open_findings = sum(1 for f in findings if f.status == "OPEN")

    findings_by_severity = defaultdict(int)
    findings_by_criterion = defaultdict(int)
    criterion_ids_with_findings = set()

    for f in findings:
        if f.status == "CONFIRMED":
            if f.severity:
                findings_by_severity[f.severity] += 1
            if f.criterion:
                criterion_code = f.criterion.criterion_id
                findings_by_criterion[criterion_code] += 1
                criterion_ids_with_findings.add(f.criterion_id)

    criteria_failed = len(criterion_ids_with_findings)

    report_stmt = (
        select(Report)
        .where(Report.evaluation_id == evaluation_id)
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    report_result = session.execute(report_stmt)
    latest_report = report_result.scalar_one_or_none()

    conformance_verdict = None
    criteria_passed = 0
    if latest_report:
        conformance_verdict = latest_report.conformance_verdict
        criteria_passed = latest_report.criteria_passed or 0

    return {
        "total_findings": total_findings,
        "confirmed_findings": confirmed_findings,
        "dismissed_findings": dismissed_findings,
        "open_findings": open_findings,
        "criteria_failed": criteria_failed,
        "criteria_passed": criteria_passed,
        "conformance_verdict": conformance_verdict,
        "findings_by_severity": dict(findings_by_severity) if findings_by_severity else None,
        "findings_by_criterion": dict(findings_by_criterion) if findings_by_criterion else None,
    }


def register_evaluation_in_series_sync(
    session,
    evaluation_id: UUID,
) -> Optional[SeriesSnapshot]:
    """
    Synchronous version of register_evaluation_in_series for Celery tasks.
    """
    eval_stmt = select(EvaluationProject).where(EvaluationProject.id == evaluation_id)
    eval_result = session.execute(eval_stmt)
    evaluation = eval_result.scalar_one_or_none()

    if evaluation is None:
        logger.warning(
            "register_evaluation_not_found_sync",
            evaluation_id=str(evaluation_id),
        )
        return None

    existing_stmt = select(SeriesSnapshot).where(
        SeriesSnapshot.evaluation_id == evaluation_id
    )
    existing_result = session.execute(existing_stmt)
    existing_snapshot = existing_result.scalar_one_or_none()

    if existing_snapshot is not None:
        return existing_snapshot

    series = get_or_create_series_sync(
        session=session,
        organisation_id=evaluation.organisation_id,
        target_url=evaluation.target_url,
    )

    metrics = _compute_snapshot_metrics_sync(session, evaluation_id)

    snapshot = SeriesSnapshot(
        series_id=series.id,
        evaluation_id=evaluation_id,
        snapshot_date=evaluation.created_at,
        total_findings=metrics["total_findings"],
        confirmed_findings=metrics["confirmed_findings"],
        dismissed_findings=metrics["dismissed_findings"],
        open_findings=metrics["open_findings"],
        criteria_failed=metrics["criteria_failed"],
        criteria_passed=metrics["criteria_passed"],
        conformance_verdict=metrics["conformance_verdict"],
        findings_by_severity=metrics["findings_by_severity"],
        findings_by_criterion=metrics["findings_by_criterion"],
    )
    session.add(snapshot)
    session.flush()

    logger.info(
        "snapshot_created_sync",
        snapshot_id=str(snapshot.id),
        series_id=str(series.id),
        evaluation_id=str(evaluation_id),
    )

    return snapshot
