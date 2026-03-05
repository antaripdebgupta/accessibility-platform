"""
Exploration API routes.

Provides endpoints for crawling/exploration functionality:
- Trigger crawl task
- List discovered pages
- Get page summary by type
"""

from typing import Optional
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from db.session import get_db
from models.evaluation import EvaluationProject
from models.page import Page
from models.user import User
from tasks import celery_app
from tasks.crawl import crawl_website

router = APIRouter(tags=["Exploration"])

# Request/Response Schemas

class ExploreRequest(BaseModel):
    """Request schema for starting exploration."""

    max_pages: int = 15
    respect_robots: bool = True


class ExploreResponse(BaseModel):
    """Response schema for exploration start."""

    task_id: str
    evaluation_id: str
    message: str


class PageResponse(BaseModel):
    """Schema for a single page."""

    id: str
    url: str
    title: Optional[str] = None
    page_type: Optional[str] = None
    http_status: Optional[int] = None
    crawl_status: str
    scan_status: str
    in_sample: bool

    class Config:
        from_attributes = True


class PageListResponse(BaseModel):
    """Paginated list of pages."""

    total: int
    items: list[PageResponse]


class PageTypeSummary(BaseModel):
    """Summary of pages grouped by type."""

    page_type: str
    count: int


class PageSummaryResponse(BaseModel):
    """Summary response for pages by type."""

    total_pages: int
    by_type: list[PageTypeSummary]

# Helper Functions

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

# Routes

@router.post(
    "/{evaluation_id}/explore",
    response_model=ExploreResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_exploration(
    evaluation_id: UUID,
    request: ExploreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExploreResponse:
    """
    Start website exploration/crawling for an evaluation.

    Triggers an async Celery task to crawl the target website
    and discover pages for accessibility evaluation.

    Args:
        evaluation_id: The evaluation UUID
        request: Exploration options (max_pages, respect_robots)

    Returns:
        ExploreResponse with task_id for polling

    Raises:
        404: Evaluation not found
        403: User doesn't have access
        409: Crawl already in progress
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Check evaluation is in a valid state for crawling
    if evaluation.status not in ("DRAFT", "SCOPING", "SAMPLING"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot start exploration in status: {evaluation.status}",
        )

    # Update status to indicate crawl starting
    evaluation.status = "EXPLORING"
    await db.commit()

    # Dispatch Celery task
    task = crawl_website.delay(
        evaluation_id=str(evaluation.id),
        target_url=evaluation.target_url,
        max_pages=request.max_pages,
        respect_robots=request.respect_robots,
    )

    return ExploreResponse(
        task_id=task.id,
        evaluation_id=str(evaluation.id),
        message="Exploration started successfully",
    )


@router.get(
    "/{evaluation_id}/pages",
    response_model=PageListResponse,
)
async def list_pages(
    evaluation_id: UUID,
    page_type: Optional[str] = Query(None, description="Filter by page type"),
    in_sample: Optional[bool] = Query(None, description="Filter by sample inclusion"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PageListResponse:
    """
    List discovered pages for an evaluation.

    Returns paginated list of pages with optional filtering.

    Args:
        evaluation_id: The evaluation UUID
        page_type: Optional filter by page classification
        in_sample: Optional filter by sample inclusion
        skip: Pagination offset (default: 0)
        limit: Max results (default: 50, max: 200)

    Returns:
        PageListResponse with total count and page items
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Build query
    base_query = select(Page).where(Page.evaluation_id == evaluation.id)

    if page_type:
        base_query = base_query.where(Page.page_type == page_type)

    if in_sample is not None:
        base_query = base_query.where(Page.in_sample == in_sample)

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = (
        base_query
        .order_by(Page.discovered_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    pages = result.scalars().all()

    items = [
        PageResponse(
            id=str(page.id),
            url=page.url,
            title=page.title,
            page_type=page.page_type,
            http_status=page.http_status,
            crawl_status=page.crawl_status,
            scan_status=page.scan_status,
            in_sample=page.in_sample,
        )
        for page in pages
    ]

    return PageListResponse(total=total, items=items)


@router.get(
    "/{evaluation_id}/pages/summary",
    response_model=PageSummaryResponse,
)
async def get_pages_summary(
    evaluation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PageSummaryResponse:
    """
    Get summary of discovered pages grouped by type.

    Returns count of pages for each page type classification.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        PageSummaryResponse with total and breakdown by type
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Get total page count
    total_query = select(func.count()).select_from(Page).where(
        Page.evaluation_id == evaluation.id
    )
    total_result = await db.execute(total_query)
    total_pages = total_result.scalar() or 0

    # Get count grouped by page type
    count_col = func.count().label("page_count")
    type_query = (
        select(Page.page_type, count_col)
        .where(Page.evaluation_id == evaluation.id)
        .group_by(Page.page_type)
        .order_by(count_col.desc())
    )
    type_result = await db.execute(type_query)
    type_rows = type_result.all()

    by_type = [
        PageTypeSummary(
            page_type=row.page_type or "unknown",
            count=row.page_count,
        )
        for row in type_rows
    ]

    return PageSummaryResponse(
        total_pages=total_pages,
        by_type=by_type,
    )
