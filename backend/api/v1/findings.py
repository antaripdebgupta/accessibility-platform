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

from core.auth import get_current_user
from core.config import settings
from db.session import get_db
from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.user import User
from models.wcag import WcagCriterion
from schemas.common import PaginatedResponse
from schemas.finding import (
    FindingCreate,
    FindingResponse,
    FindingSummary,
    FindingUpdate,
)
from storage.operations import get_presigned_url

router = APIRouter(tags=["Findings"])


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


def build_finding_response(
    finding: Finding,
    page: Optional[Page] = None,
    criterion: Optional[WcagCriterion] = None,
    include_screenshot_url: bool = False,
) -> FindingResponse:
    """
    Build a FindingResponse from a Finding model.

    Args:
        finding: The Finding ORM object
        page: Optional Page object for page_url
        criterion: Optional WcagCriterion for criterion details
        include_screenshot_url: Whether to generate presigned URL

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
    )


@router.get(
    "/{evaluation_id}/findings",
    response_model=PaginatedResponse[FindingResponse],
)
async def list_findings(
    evaluation_id: UUID,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    criterion_id: Optional[str] = Query(None, description="Filter by WCAG criterion ID (e.g., 1.1.1)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[FindingResponse]:
    """
    List findings for an evaluation with optional filters.

    Args:
        evaluation_id: The evaluation UUID
        severity: Filter by severity level
        status_filter: Filter by finding status
        source: Filter by finding source (axe-core, manual)
        criterion_id: Filter by WCAG criterion ID string
        skip: Pagination offset
        limit: Max results per page

    Returns:
        Paginated list of findings with WCAG and page details
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

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
            return PaginatedResponse(total=0, items=[])

    # Get total count
    count_query = select(func.count()).select_from(
        select(Finding).where(and_(*base_conditions)).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results with relationships
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
            include_screenshot_url=True,  # Always include URL
        )
        for f in findings
    ]

    return PaginatedResponse(total=total, items=items)


@router.get(
    "/{evaluation_id}/findings/summary",
    response_model=FindingSummary,
)
async def get_findings_summary(
    evaluation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FindingSummary:
    """
    Get summary of findings by severity for an evaluation.

    Only counts findings where status != DISMISSED.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        FindingSummary with counts by severity
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Query to count findings by severity (excluding DISMISSED)
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FindingResponse:
    """
    Create a manual finding for an evaluation.

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
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FindingResponse:
    """
    Update a finding's status, reviewer note, or remediation.

    Sets reviewed_by to the current user and updates updated_at.

    Args:
        finding_id: The finding UUID
        data: Fields to update

    Returns:
        Updated finding with full details
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

    # Apply updates
    if data.status is not None:
        finding.status = data.status

    if data.reviewer_note is not None:
        finding.reviewer_note = data.reviewer_note

    if data.remediation is not None:
        finding.remediation = data.remediation

    # Set reviewer and update timestamp
    finding.reviewed_by = user.id
    finding.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(finding)

    return build_finding_response(
        finding=finding,
        page=finding.page,
        criterion=finding.criterion,
        include_screenshot_url=True,
    )
