"""
WCAG API routes.

Provides endpoints for retrieving WCAG criteria.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from db.session import get_db
from models.user import User
from models.wcag import WcagCriterion

router = APIRouter(tags=["WCAG"])


class WcagCriterionResponse(BaseModel):
    """Response schema for WCAG criterion."""

    id: str
    criterion_id: str
    name: str
    level: str
    wcag_version: str
    description: Optional[str] = None
    understanding_url: Optional[str] = None

    class Config:
        from_attributes = True


@router.get(
    "/criteria",
    response_model=List[WcagCriterionResponse],
)
async def list_wcag_criteria(
    level: Optional[str] = Query(None, description="Filter by level (A, AA, AAA)"),
    wcag_version: Optional[str] = Query(None, description="Filter by WCAG version (2.1, 2.2)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WcagCriterionResponse]:
    """
    List all WCAG criteria.

    Args:
        level: Optional filter by conformance level
        wcag_version: Optional filter by WCAG version

    Returns:
        List of WCAG criteria
    """
    query = select(WcagCriterion).order_by(WcagCriterion.criterion_id)

    if level:
        if level.upper() not in ("A", "AA", "AAA"):
            pass  # Just ignore invalid levels
        else:
            query = query.where(WcagCriterion.level == level.upper())

    if wcag_version:
        query = query.where(WcagCriterion.wcag_version == wcag_version)

    result = await db.execute(query)
    criteria = result.scalars().all()

    return [
        WcagCriterionResponse(
            id=str(c.id),
            criterion_id=c.criterion_id,
            name=c.name,
            level=c.level,
            wcag_version=c.wcag_version,
            description=c.description,
            understanding_url=c.understanding_url,
        )
        for c in criteria
    ]
