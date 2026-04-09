"""
Sampling API routes.

Provides endpoints for WCAG-EM Step 3 page sampling:
- Compute sample based on algorithm
- View current sample state
- Manually toggle page inclusion
- Recompute sample with new config
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import require_permission, AuthenticatedUser
from core.audit import log_action, AuditAction
from db.session import get_db
from models.evaluation import EvaluationProject
from models.page import Page
from sampling.service import (
    apply_sample_to_evaluation,
    get_sample_summary,
    get_sampled_pages,
    toggle_page_sample,
    get_sampled_page_count,
)

router = APIRouter(tags=["Sampling"])


# Request/Response Schemas

class SampleConfigRequest(BaseModel):
    """Request schema for computing a sample."""

    max_sample_size: Optional[int] = Field(
        None,
        ge=5,
        le=30,
        description="Maximum pages in the combined sample (5-30)",
    )
    min_sample_size: Optional[int] = Field(
        None,
        ge=3,
        le=30,
        description="Minimum pages required in sample (3-30, capped at max_sample_size)",
    )
    random_sample_ratio: Optional[float] = Field(
        None,
        ge=0.0,
        le=0.3,
        description="Percentage of eligible pages for random selection (0-30%)",
    )
    required_page_types: Optional[list[str]] = Field(
        None,
        description="Page types that MUST be included if they exist",
    )
    manual_inclusions: Optional[list[str]] = Field(
        None,
        description="Page IDs that are always included regardless of algorithm",
    )
    manual_exclusions: Optional[list[str]] = Field(
        None,
        description="Page IDs that are always excluded",
    )


class SampleResultResponse(BaseModel):
    """Response schema for sample computation result."""

    structured_count: int
    random_count: int
    total_count: int
    coverage: dict[str, int]
    reasoning: list[str]
    sampled_page_ids: list[str]


class SampleSummaryResponse(BaseModel):
    """Response schema for sample summary."""

    total_pages: int
    sampled_pages: int
    unsampled_pages: int
    coverage: dict[str, int]


class SampledPageResponse(BaseModel):
    """Response schema for a sampled page."""

    id: str
    url: str
    title: Optional[str] = None
    page_type: str
    in_sample: bool
    sample_reason: Optional[str] = None
    http_status: Optional[int] = None
    scan_status: str = "PENDING"


class SampleDetailResponse(BaseModel):
    """Response schema for full sample details."""

    summary: SampleSummaryResponse
    pages: list[SampledPageResponse]


class TogglePageRequest(BaseModel):
    """Request schema for toggling a page's sample status."""

    in_sample: bool = Field(..., description="Whether to include the page in the sample")


# Helper Functions

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


@router.post(
    "/{evaluation_id}/sample",
    response_model=SampleResultResponse,
    status_code=status.HTTP_200_OK,
)
async def compute_sample_for_evaluation(
    evaluation_id: UUID,
    config: Optional[SampleConfigRequest] = None,
    user: AuthenticatedUser = Depends(require_permission("evaluation.advance")),
    db: AsyncSession = Depends(get_db),
) -> SampleResultResponse:
    """
    Compute page sample using WCAG-EM algorithm.

    Implements Step 3 of the W3C Website Accessibility Conformance
    Evaluation Methodology (WCAG-EM).

    The algorithm:
    1. Structured Sample: Homepage, required types, type diversity
    2. Random Sample: 10% of eligible pages for broader coverage
    3. Combined Sample: Deduplicated union, capped at max_sample_size

    All configuration is optional - sensible defaults are used.

    Requires owner or auditor role.

    Args:
        evaluation_id: The evaluation UUID
        config: Optional sampling configuration overrides

    Returns:
        SampleResultResponse with counts, coverage, reasoning, and page IDs

    Raises:
        404: Evaluation not found
        403: User doesn't have access
        400: Evaluation not in valid state for sampling
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Verify evaluation is in valid state for sampling
    valid_states = ("EXPLORING", "SAMPLING")
    if evaluation.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation must be in EXPLORING or SAMPLING status to compute sample. "
                   f"Current status: {evaluation.status}. "
                   f"Please run website exploration first.",
        )

    # Build config overrides from request
    config_overrides = config.model_dump(exclude_none=True) if config else {}

    # Run sampling algorithm
    result = await apply_sample_to_evaluation(
        evaluation_id=str(evaluation_id),
        db=db,
        config_overrides=config_overrides,
    )

    # Update evaluation status to SAMPLING if not already
    if evaluation.status == "EXPLORING":
        evaluation.status = "SAMPLING"
        await db.flush()

    await db.commit()

    return SampleResultResponse(
        structured_count=result.structured_count,
        random_count=result.random_count,
        total_count=result.total_count,
        coverage=result.coverage,
        reasoning=result.reasoning,
        sampled_page_ids=result.combined_pages,
    )


@router.get(
    "/{evaluation_id}/sample",
    response_model=SampleDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_sample_details(
    evaluation_id: UUID,
    user: AuthenticatedUser = Depends(require_permission("exploration.read")),
    db: AsyncSession = Depends(get_db),
) -> SampleDetailResponse:
    """
    Get current sample state for an evaluation.

    Returns summary statistics and list of all pages with their
    sample inclusion status.

    Args:
        evaluation_id: The evaluation UUID

    Returns:
        SampleDetailResponse with summary and pages list

    Raises:
        404: Evaluation not found
        403: User doesn't have access
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Get summary
    summary_data = await get_sample_summary(str(evaluation_id), db)
    summary = SampleSummaryResponse(**summary_data)

    # Get pages
    pages_data = await get_sampled_pages(str(evaluation_id), db)
    pages = [SampledPageResponse(**p) for p in pages_data]

    return SampleDetailResponse(
        summary=summary,
        pages=pages,
    )


@router.patch(
    "/{evaluation_id}/sample/pages/{page_id}",
    response_model=SampledPageResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_page_in_sample(
    evaluation_id: UUID,
    page_id: UUID,
    request: TogglePageRequest,
    user: AuthenticatedUser = Depends(require_permission("evaluation.advance")),
    db: AsyncSession = Depends(get_db),
) -> SampledPageResponse:
    """
    Manually toggle a page's sample inclusion.

    Use this to manually include or exclude specific pages from
    the sample after algorithm computation.

    Returns 400 if removing would drop below minimum sample size.

    Args:
        evaluation_id: The evaluation UUID
        page_id: The page UUID to toggle
        request: Toggle request with in_sample boolean

    Returns:
        Updated page details

    Raises:
        404: Evaluation or page not found
        403: User doesn't have access
        400: Would violate minimum sample size
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # If removing from sample, check minimum size
    if not request.in_sample:
        # Get current sample count
        current_count = await get_sampled_page_count(str(evaluation_id), db)

        # Get min_sample_size from config
        min_size = 5  # Default
        if evaluation.scope_config and "sampling_config" in evaluation.scope_config:
            min_size = evaluation.scope_config["sampling_config"].get("min_sample_size", 5)

        # Check if page is currently in sample
        page_stmt = select(Page.in_sample).where(
            Page.id == page_id,
            Page.evaluation_id == evaluation_id,
        )
        page_result = await db.execute(page_stmt)
        is_in_sample = page_result.scalar()

        if is_in_sample and current_count <= min_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove page from sample. Minimum sample size is {min_size} pages. "
                       f"Currently have {current_count} pages in sample.",
            )

    try:
        updated_page = await toggle_page_sample(
            evaluation_id=str(evaluation_id),
            page_id=str(page_id),
            in_sample=request.in_sample,
            db=db,
        )
        await db.commit()
        return SampledPageResponse(**updated_page)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{evaluation_id}/sample/recompute",
    response_model=SampleResultResponse,
    status_code=status.HTTP_200_OK,
)
async def recompute_sample(
    evaluation_id: UUID,
    config: Optional[SampleConfigRequest] = None,
    user: AuthenticatedUser = Depends(require_permission("evaluation.advance")),
    db: AsyncSession = Depends(get_db),
) -> SampleResultResponse:
    """
    Re-run the sampling algorithm with current or new config.

    This is useful when:
    - New pages have been discovered after initial sampling
    - You want to apply different configuration
    - Manual toggles need to be reset

    WARNING: This will reset all manual page toggles.

    Args:
        evaluation_id: The evaluation UUID
        config: Optional new configuration to apply

    Returns:
        SampleResultResponse with new sample results

    Raises:
        404: Evaluation not found
        403: User doesn't have access
        400: Evaluation not in valid state
    """
    evaluation = await get_evaluation_for_user(evaluation_id, user, db)

    # Verify evaluation is in valid state
    valid_states = ("EXPLORING", "SAMPLING")
    if evaluation.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation must be in EXPLORING or SAMPLING status to recompute sample. "
                   f"Current status: {evaluation.status}.",
        )

    # Build config overrides from request
    config_overrides = config.model_dump(exclude_none=True) if config else {}

    # Re-run sampling algorithm
    result = await apply_sample_to_evaluation(
        evaluation_id=str(evaluation_id),
        db=db,
        config_overrides=config_overrides,
    )

    await db.commit()

    return SampleResultResponse(
        structured_count=result.structured_count,
        random_count=result.random_count,
        total_count=result.total_count,
        coverage=result.coverage,
        reasoning=result.reasoning,
        sampled_page_ids=result.combined_pages,
    )
