"""
WCAG-EM Sampling Service.

Database integration layer for the sampling engine.
Handles applying sample results to evaluation pages and retrieving sample state.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from models.evaluation import EvaluationProject
from models.page import Page
from sampling.engine import compute_sample, SampleConfig, SampleResult

logger = get_logger(__name__)


async def apply_sample_to_evaluation(
    evaluation_id: str | UUID,
    db: AsyncSession,
    config_overrides: Optional[dict] = None,
) -> SampleResult:
    """
    Apply WCAG-EM sampling algorithm to an evaluation's pages.

    This function:
    1. Fetches all pages for the evaluation
    2. Merges scope_config with any overrides
    3. Runs the sampling algorithm
    4. Updates all pages' in_sample flags in the database
    5. Stores the final config in evaluation.scope_config for audit trail

    Args:
        evaluation_id: Evaluation UUID (string or UUID object)
        db: Async database session
        config_overrides: Optional dict to override scope_config values

    Returns:
        SampleResult with selected pages, counts, coverage, and reasoning

    Raises:
        ValueError: If evaluation not found
    """
    if isinstance(evaluation_id, str):
        eval_uuid = UUID(evaluation_id)
    else:
        eval_uuid = evaluation_id

    # Fetch evaluation
    eval_stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
    eval_result = await db.execute(eval_stmt)
    evaluation = eval_result.scalar_one_or_none()

    if evaluation is None:
        raise ValueError(f"Evaluation not found: {evaluation_id}")

    # Fetch all pages for this evaluation
    pages_stmt = select(Page).where(Page.evaluation_id == eval_uuid)
    pages_result = await db.execute(pages_stmt)
    pages = pages_result.scalars().all()

    if not pages:
        logger.warning(
            "sampling_no_pages",
            evaluation_id=str(evaluation_id),
        )
        return SampleResult(
            reasoning=["No pages found for this evaluation. Run exploration first."]
        )

    # Build pages list for algorithm
    pages_data = [
        {
            "id": str(page.id),
            "url": page.url,
            "title": page.title,
            "page_type": page.page_type,
            "http_status": page.http_status,
        }
        for page in pages
    ]

    # Merge config: start with defaults, apply scope_config, then overrides
    base_config = {
        "max_sample_size": 15,
        "min_sample_size": 5,
        "random_sample_ratio": 0.1,
        "required_page_types": [],
        "manual_inclusions": [],
        "manual_exclusions": [],
        "evaluation_id": str(eval_uuid),
    }

    # Apply existing scope_config if present
    if evaluation.scope_config:
        for key in base_config:
            if key in evaluation.scope_config:
                base_config[key] = evaluation.scope_config[key]

    # Apply overrides
    if config_overrides:
        for key, value in config_overrides.items():
            if key in base_config and value is not None:
                base_config[key] = value

    # Always ensure evaluation_id is set for reproducible sampling
    base_config["evaluation_id"] = str(eval_uuid)

    logger.info(
        "sampling_compute_start",
        evaluation_id=str(evaluation_id),
        total_pages=len(pages_data),
        config=base_config,
    )

    # Run sampling algorithm
    config = SampleConfig(**base_config)
    result = compute_sample(pages_data, config)

    # Update database: set all pages to in_sample = False
    reset_stmt = (
        update(Page)
        .where(Page.evaluation_id == eval_uuid)
        .values(in_sample=False, sample_reason=None)
    )
    await db.execute(reset_stmt)

    # Build lookup for sample reason
    structured_set = set(result.structured_pages)
    random_set = set(result.random_pages)

    # Update sampled pages to in_sample = True with reason
    for page_id in result.combined_pages:
        # Determine reason
        if page_id in structured_set:
            reason = "structured"
        elif page_id in random_set:
            reason = "random"
        else:
            reason = "minimum"

        sample_stmt = (
            update(Page)
            .where(Page.id == UUID(page_id))
            .values(in_sample=True, sample_reason=reason)
        )
        await db.execute(sample_stmt)

    # Update evaluation scope_config with final config used (audit trail)
    final_scope_config = evaluation.scope_config.copy() if evaluation.scope_config else {}
    final_scope_config.update({
        "sampling_config": config.to_dict(),
        "last_sampled_at": datetime.utcnow().isoformat(),
        "sample_result": {
            "structured_count": result.structured_count,
            "random_count": result.random_count,
            "total_count": result.total_count,
            "coverage": result.coverage,
        },
    })
    evaluation.scope_config = final_scope_config
    evaluation.updated_at = datetime.utcnow()

    await db.flush()

    logger.info(
        "sampling_compute_complete",
        evaluation_id=str(evaluation_id),
        structured_count=result.structured_count,
        random_count=result.random_count,
        total_count=result.total_count,
        coverage=result.coverage,
    )

    return result


async def get_sample_summary(
    evaluation_id: str | UUID,
    db: AsyncSession,
) -> dict:
    """
    Get summary of current sample state for an evaluation.

    Args:
        evaluation_id: Evaluation UUID (string or UUID object)
        db: Async database session

    Returns:
        Dictionary with:
        - total_pages: Total discovered pages
        - sampled_pages: Pages with in_sample=True
        - unsampled_pages: Pages with in_sample=False
        - coverage: Page type → count in sample

    Raises:
        ValueError: If evaluation not found
    """
    if isinstance(evaluation_id, str):
        eval_uuid = UUID(evaluation_id)
    else:
        eval_uuid = evaluation_id

    # Verify evaluation exists
    eval_stmt = select(EvaluationProject.id).where(EvaluationProject.id == eval_uuid)
    eval_result = await db.execute(eval_stmt)
    if eval_result.scalar_one_or_none() is None:
        raise ValueError(f"Evaluation not found: {evaluation_id}")

    # Count total pages
    total_stmt = select(func.count()).select_from(Page).where(
        Page.evaluation_id == eval_uuid
    )
    total_result = await db.execute(total_stmt)
    total_pages = total_result.scalar() or 0

    # Count sampled pages
    sampled_stmt = select(func.count()).select_from(Page).where(
        Page.evaluation_id == eval_uuid,
        Page.in_sample == True,  # noqa: E712
    )
    sampled_result = await db.execute(sampled_stmt)
    sampled_pages = sampled_result.scalar() or 0

    # Get coverage by page type for sampled pages
    coverage_stmt = (
        select(Page.page_type, func.count().label("count"))
        .where(
            Page.evaluation_id == eval_uuid,
            Page.in_sample == True,  # noqa: E712
        )
        .group_by(Page.page_type)
    )
    coverage_result = await db.execute(coverage_stmt)
    coverage_rows = coverage_result.all()

    coverage = {
        (row.page_type or "other"): row.count
        for row in coverage_rows
    }

    return {
        "total_pages": total_pages,
        "sampled_pages": sampled_pages,
        "unsampled_pages": total_pages - sampled_pages,
        "coverage": coverage,
    }


async def get_sampled_pages(
    evaluation_id: str | UUID,
    db: AsyncSession,
) -> list[dict]:
    """
    Get list of all pages with their sample status.

    Args:
        evaluation_id: Evaluation UUID (string or UUID object)
        db: Async database session

    Returns:
        List of page dictionaries with id, url, title, page_type,
        in_sample, sample_reason, http_status
    """
    if isinstance(evaluation_id, str):
        eval_uuid = UUID(evaluation_id)
    else:
        eval_uuid = evaluation_id

    pages_stmt = (
        select(Page)
        .where(Page.evaluation_id == eval_uuid)
        .order_by(Page.in_sample.desc(), Page.discovered_at.asc())
    )
    pages_result = await db.execute(pages_stmt)
    pages = pages_result.scalars().all()

    return [
        {
            "id": str(page.id),
            "url": page.url,
            "title": page.title,
            "page_type": page.page_type or "other",
            "in_sample": page.in_sample,
            "sample_reason": page.sample_reason,
            "http_status": page.http_status,
            "scan_status": page.scan_status,
        }
        for page in pages
    ]


async def toggle_page_sample(
    evaluation_id: str | UUID,
    page_id: str | UUID,
    in_sample: bool,
    db: AsyncSession,
) -> dict:
    """
    Manually toggle a single page's sample inclusion.

    Args:
        evaluation_id: Evaluation UUID
        page_id: Page UUID
        in_sample: Whether to include in sample
        db: Async database session

    Returns:
        Updated page dictionary

    Raises:
        ValueError: If page not found or doesn't belong to evaluation
    """
    if isinstance(evaluation_id, str):
        eval_uuid = UUID(evaluation_id)
    else:
        eval_uuid = evaluation_id

    if isinstance(page_id, str):
        page_uuid = UUID(page_id)
    else:
        page_uuid = page_id

    # Fetch page
    page_stmt = select(Page).where(
        Page.id == page_uuid,
        Page.evaluation_id == eval_uuid,
    )
    page_result = await db.execute(page_stmt)
    page = page_result.scalar_one_or_none()

    if page is None:
        raise ValueError(f"Page not found: {page_id}")

    # Update page
    page.in_sample = in_sample
    page.sample_reason = "manual" if in_sample else None

    await db.flush()

    logger.info(
        "sampling_page_toggled",
        evaluation_id=str(evaluation_id),
        page_id=str(page_id),
        in_sample=in_sample,
    )

    return {
        "id": str(page.id),
        "url": page.url,
        "title": page.title,
        "page_type": page.page_type or "other",
        "in_sample": page.in_sample,
        "sample_reason": page.sample_reason,
        "http_status": page.http_status,
        "scan_status": page.scan_status,
    }


async def get_sampled_page_count(
    evaluation_id: str | UUID,
    db: AsyncSession,
) -> int:
    """
    Get count of pages with in_sample=True for an evaluation.

    Args:
        evaluation_id: Evaluation UUID
        db: Async database session

    Returns:
        Number of sampled pages
    """
    if isinstance(evaluation_id, str):
        eval_uuid = UUID(evaluation_id)
    else:
        eval_uuid = evaluation_id

    count_stmt = select(func.count()).select_from(Page).where(
        Page.evaluation_id == eval_uuid,
        Page.in_sample == True,  # noqa: E712
    )
    result = await db.execute(count_stmt)
    return result.scalar() or 0
