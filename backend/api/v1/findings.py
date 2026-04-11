"""
Findings API routes.

Provides CRUD endpoints for accessibility findings.
Includes listing, filtering, summary, and status updates.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user, require_permission, AuthenticatedUser
from core.audit import log_action, AuditAction
from core.config import settings
from core.logging import get_logger
from core.permissions import can
from db.session import get_db
from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.wcag import WcagCriterion
from schemas.common import PaginatedResponse
from schemas.finding import (
    FindingCreate,
    FindingResponse,
    FindingSummary,
    FindingUpdate,
    FindingsWithProfileResponse,
    ProfileSummaryInline,
)
from storage.operations import get_presigned_url
from profiles.definitions import get_profile
from profiles.engine import apply_profile_to_findings, filter_by_profile, get_profile_summary
from longitudinal.series import update_snapshot

router = APIRouter(tags=["Findings"])
logger = get_logger(__name__)


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


def build_finding_response(
    finding: Finding,
    page: Optional[Page] = None,
    criterion: Optional[WcagCriterion] = None,
    include_screenshot_url: bool = False,
    profile_data: Optional[dict] = None,
) -> FindingResponse:
    """
    Build a FindingResponse from a Finding model.

    Args:
        finding: The Finding ORM object
        page: Optional Page object for page_url
        criterion: Optional WcagCriterion for criterion details
        include_screenshot_url: Whether to generate presigned URL
        profile_data: Optional dict with profile_relevant, profile_priority, profile_severity

    Returns:
        FindingResponse schema object
    """
    screenshot_url = None
    if include_screenshot_url and finding.screenshot_key:
        screenshot_url = get_presigned_url(
            bucket=settings.minio_bucket_screenshots,
            key=finding.screenshot_key,
            expires_hours=24,
        )

    # Extract profile fields if provided
    profile_relevant = profile_data.get("profile_relevant") if profile_data else None
    profile_priority = profile_data.get("profile_priority") if profile_data else None
    profile_severity = profile_data.get("profile_severity") if profile_data else None

    return FindingResponse(
        id=finding.id,
        evaluation_id=finding.evaluation_id,
        page_id=finding.page_id,
        criterion_id=finding.criterion_id,
        criterion_code=criterion.criterion_id if criterion else None,
        criterion_name=criterion.name if criterion else None,
        criterion_level=criterion.level if criterion else None,
        page_url=page.url if page else None,
        source=finding.source,
        rule_id=finding.rule_id,
        description=finding.description,
        severity=finding.severity,
        css_selector=finding.css_selector,
        html_snippet=finding.html_snippet,
        impact=finding.impact,
        remediation=finding.remediation,
        status=finding.status,
        reviewed_by=finding.reviewed_by,
        reviewer_note=finding.reviewer_note,
        screenshot_key=finding.screenshot_key,
        screenshot_url=screenshot_url,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
        profile_relevant=profile_relevant,
        profile_priority=profile_priority,
        profile_severity=profile_severity,
    )


@router.get(
    "/{evaluation_id}/findings",
    response_model=FindingsWithProfileResponse,
)
async def list_findings(
    evaluation_id: UUID,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    criterion_id: Optional[str] = Query(None, description="Filter by WCAG criterion ID (e.g., 1.1.1)"),
    profile: Optional[str] = Query(None, description="Disability profile ID (blind, low_vision, motor, cognitive)"),
    exclude_na: bool = Query(False, description="Exclude findings marked N/A for the profile"),
    profile_priority_filter: Optional[str] = Query(None, alias="profile_priority", description="Filter by profile priority (critical, high, medium, low, na)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    user: AuthenticatedUser = Depends(require_permission("finding.read")),
    db: AsyncSession = Depends(get_db),
) -> FindingsWithProfileResponse:
    """
    List findings for an evaluation with optional filters and profile-based enrichment.

    When a profile is specified, each finding is enriched with:
    - profile_relevant: Whether this criterion is relevant for the profile
    - profile_priority: Priority level (critical/high/medium/low/na) for this profile
    - profile_severity: Boosted severity for this profile

    Args:
        evaluation_id: The evaluation UUID
        severity: Filter by severity level
        status_filter: Filter by finding status
        source: Filter by finding source (axe-core, manual)
        criterion_id: Filter by WCAG criterion ID string
        profile: Disability profile ID to apply
        exclude_na: If true, exclude findings marked N/A for the profile
        profile_priority_filter: Filter by profile priority level
        skip: Pagination offset
        limit: Max results per page

    Returns:
        FindingsWithProfileResponse with findings and optional profile summary
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Validate profile if provided
    profile_obj = None
    if profile:
        profile_obj = get_profile(profile)
        if profile_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile. Must be one of: blind, low_vision, motor, cognitive",
            )

    # Build base query
    base_conditions = [Finding.evaluation_id == evaluation_id]

    # Apply filters
    if severity:
        valid_severities = ("critical", "serious", "moderate", "minor", "info")
        if severity.lower() not in valid_severities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity. Must be one of: {', '.join(valid_severities)}",
            )
        base_conditions.append(Finding.severity == severity.lower())

    if status_filter:
        valid_statuses = ("OPEN", "CONFIRMED", "DISMISSED", "RESOLVED", "WONT_FIX")
        if status_filter.upper() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        base_conditions.append(Finding.status == status_filter.upper())

    if source:
        valid_sources = ("axe-core", "pa11y", "manual")
        if source.lower() not in valid_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}",
            )
        base_conditions.append(Finding.source == source.lower())

    # Handle criterion_id filter (need to join with WcagCriterion)
    criterion_uuid = None
    if criterion_id:
        criterion_stmt = select(WcagCriterion).where(WcagCriterion.criterion_id == criterion_id)
        criterion_result = await db.execute(criterion_stmt)
        criterion = criterion_result.scalar_one_or_none()
        if criterion:
            criterion_uuid = criterion.id
            base_conditions.append(Finding.criterion_id == criterion_uuid)
        else:
            # No matching criterion, return empty result
            return FindingsWithProfileResponse(total=0, items=[], profile_summary=None)

    # Get total count (before profile filtering for accurate total)
    count_query = select(func.count()).select_from(
        select(Finding).where(and_(*base_conditions)).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get ALL results with relationships for profile processing
    # We need to fetch all findings first if profile is active to apply profile filtering
    if profile_obj:
        # Fetch all findings to apply profile filtering and sorting
        query = (
            select(Finding)
            .options(
                selectinload(Finding.page),
                selectinload(Finding.criterion),
            )
            .where(and_(*base_conditions))
        )
        result = await db.execute(query)
        all_findings = result.scalars().all()

        # Convert to dicts for profile processing
        findings_dicts = []
        for f in all_findings:
            findings_dicts.append({
                "finding": f,
                "criterion_code": f.criterion.criterion_id if f.criterion else None,
                "severity": f.severity,
            })

        # Apply profile to get priority and severity info
        # profile is guaranteed to be non-None here since profile_obj exists
        profile_id: str = profile  # type: ignore[assignment]
        enriched_findings = apply_profile_to_findings(findings_dicts, profile_id)

        # Apply profile priority filter if specified
        if profile_priority_filter:
            valid_priorities = ("critical", "high", "medium", "low", "na")
            if profile_priority_filter.lower() not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid profile_priority. Must be one of: {', '.join(valid_priorities)}",
                )
            enriched_findings = [
                f for f in enriched_findings
                if f.get("profile_priority") == profile_priority_filter.lower()
            ]

        # Filter out N/A findings if requested
        if exclude_na:
            enriched_findings = [
                f for f in enriched_findings
                if f.get("profile_priority") != "na"
            ]

        # Sort by profile_priority then profile_severity
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "na": 4}
        severity_order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3, "info": 4}

        enriched_findings.sort(
            key=lambda f: (
                priority_order.get(f.get("profile_priority", "medium"), 2),
                severity_order.get(f.get("profile_severity", "moderate"), 2),
            )
        )

        # Update total to reflect filtered count
        total = len(enriched_findings)

        # Apply pagination
        paginated_findings = enriched_findings[skip:skip + limit]

        # Build response items
        items = []
        for ef in paginated_findings:
            finding = ef["finding"]
            items.append(
                build_finding_response(
                    finding=finding,
                    page=finding.page,
                    criterion=finding.criterion,
                    include_screenshot_url=True,
                    profile_data={
                        "profile_relevant": ef.get("profile_relevant"),
                        "profile_priority": ef.get("profile_priority"),
                        "profile_severity": ef.get("profile_severity"),
                    },
                )
            )

        # Compute profile summary for all findings (before pagination)
        all_findings_for_summary = [
            {
                "criterion_code": f.criterion.criterion_id if f.criterion else None,
                "severity": f.severity,
            }
            for f in all_findings
        ]
        summary_data = get_profile_summary(all_findings_for_summary, profile_id)
        profile_summary = ProfileSummaryInline(
            profile_id=summary_data["profile_id"],
            profile_name=summary_data["profile_name"],
            critical_for_profile=summary_data["critical_for_profile"],
            high_for_profile=summary_data["high_for_profile"],
            not_applicable=summary_data["not_applicable"],
            total_relevant=summary_data["total_relevant"],
            boosted_count=summary_data["boosted_count"],
        )

        return FindingsWithProfileResponse(
            total=total,
            items=items,
            profile_summary=profile_summary,
        )

    else:
        # No profile - use standard sorting and pagination
        query = (
            select(Finding)
            .options(
                selectinload(Finding.page),
                selectinload(Finding.criterion),
            )
            .where(and_(*base_conditions))
            .order_by(
                # Order by severity priority
                case(
                    (Finding.severity == "critical", 1),
                    (Finding.severity == "serious", 2),
                    (Finding.severity == "moderate", 3),
                    (Finding.severity == "minor", 4),
                    (Finding.severity == "info", 5),
                    else_=6,
                ),
                Finding.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        findings = result.scalars().all()

        items = [
            build_finding_response(
                finding=f,
                page=f.page,
                criterion=f.criterion,
                include_screenshot_url=True,
            )
            for f in findings
        ]

        return FindingsWithProfileResponse(total=total, items=items, profile_summary=None)


@router.get(
    "/{evaluation_id}/findings/summary",
    response_model=FindingSummary,
)
async def get_findings_summary(
    evaluation_id: UUID,
    profile: Optional[str] = Query(None, description="Disability profile ID for profile-aware summary"),
    user: AuthenticatedUser = Depends(require_permission("finding.read")),
    db: AsyncSession = Depends(get_db),
) -> FindingSummary | ProfileSummaryInline:
    """
    Get summary of findings by severity for an evaluation.

    If a profile is specified, returns profile-aware summary with priority counts.
    Only counts findings where status != DISMISSED.

    Args:
        evaluation_id: The evaluation UUID
        profile: Optional profile ID for profile-aware summary

    Returns:
        FindingSummary with counts by severity, or ProfileSummaryInline if profile specified
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # If profile is specified, return profile summary
    if profile:
        profile_obj = get_profile(profile)
        if profile_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile. Must be one of: blind, low_vision, motor, cognitive",
            )

        # Fetch all findings with criteria for profile processing
        query = (
            select(Finding)
            .options(selectinload(Finding.criterion))
            .where(
                and_(
                    Finding.evaluation_id == evaluation_id,
                    Finding.status != "DISMISSED",
                )
            )
        )
        result = await db.execute(query)
        all_findings = result.scalars().all()

        # Convert to dicts for profile processing
        findings_for_summary = [
            {
                "criterion_code": f.criterion.criterion_id if f.criterion else None,
                "severity": f.severity,
            }
            for f in all_findings
        ]

        summary_data = get_profile_summary(findings_for_summary, profile)
        return ProfileSummaryInline(
            profile_id=summary_data["profile_id"],
            profile_name=summary_data["profile_name"],
            critical_for_profile=summary_data["critical_for_profile"],
            high_for_profile=summary_data["high_for_profile"],
            not_applicable=summary_data["not_applicable"],
            total_relevant=summary_data["total_relevant"],
            boosted_count=summary_data["boosted_count"],
        )

    # Standard severity summary (no profile)
    query = (
        select(Finding.severity, func.count(Finding.id))
        .where(
            and_(
                Finding.evaluation_id == evaluation_id,
                Finding.status != "DISMISSED",
            )
        )
        .group_by(Finding.severity)
    )

    result = await db.execute(query)
    severity_counts: dict[str, int] = {row[0]: row[1] for row in result.all()}

    critical = severity_counts.get("critical", 0)
    serious = severity_counts.get("serious", 0)
    moderate = severity_counts.get("moderate", 0)
    minor = severity_counts.get("minor", 0)
    info = severity_counts.get("info", 0)
    total = critical + serious + moderate + minor + info

    return FindingSummary(
        critical=critical,
        serious=serious,
        moderate=moderate,
        minor=minor,
        info=info,
        total=total,
    )


@router.post(
    "/{evaluation_id}/findings",
    response_model=FindingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_finding(
    evaluation_id: UUID,
    data: FindingCreate,
    user: AuthenticatedUser = Depends(require_permission("finding.create_manual")),
    db: AsyncSession = Depends(get_db),
) -> FindingResponse:
    """
    Create a manual finding for an evaluation.

    Requires owner or auditor role.

    Args:
        evaluation_id: The evaluation UUID
        data: Finding creation data

    Returns:
        Created finding with full details
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Verify page belongs to this evaluation
    page_stmt = select(Page).where(
        and_(
            Page.id == data.page_id,
            Page.evaluation_id == evaluation_id,
        )
    )
    page_result = await db.execute(page_stmt)
    page = page_result.scalar_one_or_none()

    if page is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page not found or does not belong to this evaluation",
        )

    # Verify criterion exists
    criterion_stmt = select(WcagCriterion).where(WcagCriterion.id == data.criterion_id)
    criterion_result = await db.execute(criterion_stmt)
    criterion = criterion_result.scalar_one_or_none()

    if criterion is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WCAG criterion not found",
        )

    # Create finding
    finding = Finding(
        evaluation_id=evaluation_id,
        page_id=data.page_id,
        criterion_id=data.criterion_id,
        source="manual",
        description=data.description,
        severity=data.severity,
        css_selector=data.css_selector,
        html_snippet=data.html_snippet,
        status="OPEN",
        reviewed_by=user.id,
    )

    db.add(finding)
    await db.flush()
    await db.refresh(finding)

    # Log the action
    await log_action(
        db=db,
        action=AuditAction.FINDING_CREATED,
        entity_type="finding",
        entity_id=str(finding.id),
        user_id=str(user.id),
        organisation_id=str(evaluation.organisation_id),
        after_state={
            "source": "manual",
            "severity": data.severity,
            "description": data.description[:200] if data.description else None,
        },
    )

    return build_finding_response(
        finding=finding,
        page=page,
        criterion=criterion,
        include_screenshot_url=False,
    )


@router.get(
    "/findings/{finding_id}",
    response_model=FindingResponse,
)
async def get_finding(
    finding_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("finding.read")),
    db: AsyncSession = Depends(get_db),
) -> FindingResponse:
    """
    Get a single finding by ID.

    Includes presigned screenshot URL if available.

    Args:
        finding_id: The finding UUID

    Returns:
        Finding with full details and screenshot URL
    """
    # Fetch finding with relationships
    stmt = (
        select(Finding)
        .options(
            selectinload(Finding.page),
            selectinload(Finding.criterion),
            selectinload(Finding.evaluation),
        )
        .where(Finding.id == finding_id)
    )
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()

    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    # Verify user has access to the evaluation's organisation
    user_org_ids = [role.organisation_id for role in user.organisation_roles]
    if finding.evaluation.organisation_id not in user_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this finding",
        )

    return build_finding_response(
        finding=finding,
        page=finding.page,
        criterion=finding.criterion,
        include_screenshot_url=True,
    )


@router.patch(
    "/findings/{finding_id}",
    response_model=FindingResponse,
)
async def update_finding(
    finding_id: UUID,
    data: FindingUpdate,
    user: AuthenticatedUser = Depends(require_permission("finding.confirm")),
    db: AsyncSession = Depends(get_db),
) -> FindingResponse:
    """
    Update a finding's status, reviewer note, or remediation.

    Requires owner, auditor, or reviewer role.
    Reviewer can only confirm or dismiss - reopen requires owner/auditor.
    Sets reviewed_by to the current user and updates updated_at.

    Args:
        finding_id: The finding UUID
        data: Fields to update

    Returns:
        Updated finding with full details
    """
    # Check if user is trying to reopen - requires elevated permission
    if data.status == "OPEN":
        if not user.can("finding.reopen"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reopening findings requires owner or auditor role",
            )

    # Fetch finding with relationships
    stmt = (
        select(Finding)
        .options(
            selectinload(Finding.page),
            selectinload(Finding.criterion),
            selectinload(Finding.evaluation),
        )
        .where(Finding.id == finding_id)
    )
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()

    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    # Verify user has access to the evaluation's organisation
    user_org_ids = [role.organisation_id for role in user.organisation_roles]
    if finding.evaluation.organisation_id not in user_org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this finding",
        )

    # Capture before state for audit logging
    before_state = {
        "status": finding.status,
        "reviewer_note": finding.reviewer_note,
    }

    # Apply updates
    new_status = None
    if data.status is not None:
        new_status = data.status
        finding.status = data.status

    if data.reviewer_note is not None:
        finding.reviewer_note = data.reviewer_note

    if data.remediation is not None:
        finding.remediation = data.remediation

    # Set reviewer and update timestamp
    finding.reviewed_by = user.id
    finding.updated_at = datetime.utcnow()

    # Determine audit action based on status change
    if new_status == "CONFIRMED":
        action = AuditAction.FINDING_CONFIRMED
    elif new_status == "DISMISSED":
        action = AuditAction.FINDING_DISMISSED
    elif new_status == "OPEN":
        action = AuditAction.FINDING_REOPENED
    else:
        action = AuditAction.FINDING_UPDATED

    # Capture after state
    after_state = {
        "status": finding.status,
        "reviewer_note": finding.reviewer_note,
    }

    # Log the action (added to session but not committed yet)
    await log_action(
        db=db,
        action=action,
        entity_type="finding",
        entity_id=str(finding.id),
        user_id=str(user.id),
        organisation_id=str(finding.evaluation.organisation_id),
        before_state=before_state,
        after_state=after_state,
    )

    # Commit both the finding update and audit log together
    await db.commit()

    # Update longitudinal snapshot to reflect finding status change (fire-and-forget)
    if new_status in ("CONFIRMED", "DISMISSED", "OPEN"):
        try:
            await update_snapshot(db, finding.evaluation_id)
            await db.commit()
            logger.debug(
                "longitudinal_snapshot_updated",
                finding_id=str(finding_id),
                evaluation_id=str(finding.evaluation_id),
                new_status=new_status,
            )
        except Exception as snapshot_error:
            # Snapshot update failure must NOT fail the finding update
            logger.warning(
                "longitudinal_snapshot_update_failed",
                finding_id=str(finding_id),
                evaluation_id=str(finding.evaluation_id),
                error=str(snapshot_error),
            )
            # Rollback snapshot changes but finding update already committed
            await db.rollback()

    # Re-fetch with relationships after commit
    stmt = (
        select(Finding)
        .options(
            selectinload(Finding.page),
            selectinload(Finding.criterion),
        )
        .where(Finding.id == finding_id)
    )
    result = await db.execute(stmt)
    finding = result.scalar_one()

    return build_finding_response(
        finding=finding,
        page=finding.page,
        criterion=finding.criterion,
        include_screenshot_url=True,
    )
