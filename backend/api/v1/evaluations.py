"""
Evaluation API routes.

Provides CRUD endpoints for evaluation projects.
All routes are scoped to the user's organisation(s).

Firestore Sync:
- POST, PATCH, and DELETE routes sync to Firestore as a background task
- Firestore failures are logged but never block the API response
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user, get_current_org
from core.firestore import sync_evaluation_to_firestore, delete_evaluation_from_firestore
from db.session import get_db
from models.user import User
from models.user_org_role import UserOrganisationRole
from models.evaluation import EvaluationProject
from models.organisation import Organisation
from schemas.common import PaginatedResponse
from schemas.evaluation import (
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationResponse,
    EvaluationListItem,
)

router = APIRouter(tags=["Evaluations"])


async def _get_user_org_ids(user: User) -> list[UUID]:
    """Get list of organisation IDs the user belongs to."""
    return [role.organisation_id for role in user.organisation_roles]


@router.get("", response_model=PaginatedResponse[EvaluationListItem])
async def list_evaluations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EvaluationListItem]:
    """List evaluation projects for the user's organisations.

    Returns paginated list of evaluation projects that belong to any
    organisation the user is a member of.

    Args:
        status_filter: Optional filter by evaluation status
        skip: Pagination offset (default: 0)
        limit: Maximum results per page (default: 20, max: 100)

    Returns:
        PaginatedResponse with total count and list of EvaluationListItem
    """
    org_ids = await _get_user_org_ids(user)

    if not org_ids:
        return PaginatedResponse(total=0, items=[])

    # Build base query with organisation scoping
    base_query = select(EvaluationProject).where(
        EvaluationProject.organisation_id.in_(org_ids),
        EvaluationProject.status != "DELETED",
    )

    # Apply status filter if provided
    if status_filter:
        valid_statuses = ["DRAFT", "SCOPING", "EXPLORING", "SAMPLING", "AUDITING", "REPORTING", "COMPLETE"]
        if status_filter.upper() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
            )
        base_query = base_query.where(EvaluationProject.status == status_filter.upper())

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = (
        base_query
        .order_by(EvaluationProject.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    evaluations = result.scalars().all()

    items = [
        EvaluationListItem(
            id=e.id,
            title=e.title,
            target_url=e.target_url,
            status=e.status,
            wcag_version=e.wcag_version,
            conformance_level=e.conformance_level,
            created_at=e.created_at,
        )
        for e in evaluations
    ]

    return PaginatedResponse(total=total, items=items)


@router.post("", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    data: EvaluationCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Create a new evaluation project.

    Creates a new evaluation project in the user's first organisation.
    If the user doesn't belong to any organisation, returns a 400 error.

    Syncs the created evaluation to Firestore as a background task.

    Args:
        data: Evaluation creation data
        background_tasks: FastAPI BackgroundTasks for Firestore sync

    Returns:
        EvaluationResponse: Created evaluation project
    """
    # Get user's first organisation (primary org)
    if not user.organisation_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to an organisation to create evaluations. Please contact an administrator.",
        )

    org_role = user.organisation_roles[0]

    # Create the evaluation project
    evaluation = EvaluationProject(
        organisation_id=org_role.organisation_id,
        created_by=user.id,
        title=data.title,
        target_url=data.target_url,
        wcag_version=data.wcag_version,
        conformance_level=data.conformance_level,
        audit_type=data.audit_type,
        status="DRAFT",
    )

    db.add(evaluation)
    await db.flush()

    # Build response
    response = EvaluationResponse(
        id=evaluation.id,
        organisation_id=evaluation.organisation_id,
        created_by=evaluation.created_by,
        title=evaluation.title,
        target_url=evaluation.target_url,
        wcag_version=evaluation.wcag_version,
        conformance_level=evaluation.conformance_level,
        audit_type=evaluation.audit_type,
        status=evaluation.status,
        scope_config=evaluation.scope_config,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )

    # Sync to Firestore as background task (fire-and-forget)
    evaluation_dict = {
        "id": evaluation.id,
        "organisation_id": evaluation.organisation_id,
        "created_by": evaluation.created_by,
        "title": evaluation.title,
        "target_url": evaluation.target_url,
        "wcag_version": evaluation.wcag_version,
        "conformance_level": evaluation.conformance_level,
        "audit_type": evaluation.audit_type,
        "status": evaluation.status,
        "created_at": evaluation.created_at,
        "updated_at": evaluation.updated_at,
    }
    background_tasks.add_task(sync_evaluation_to_firestore, evaluation_dict)

    return response


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Get a single evaluation project by ID.

    Returns the full evaluation project details if the user has access.

    Args:
        evaluation_id: UUID of the evaluation project

    Returns:
        EvaluationResponse: Full evaluation project details

    Raises:
        HTTPException(404): If evaluation doesn't exist
        HTTPException(403): If user doesn't have access to the evaluation
    """
    org_ids = await _get_user_org_ids(user)

    # Fetch evaluation with organisation scoping
    stmt = select(EvaluationProject).where(
        EvaluationProject.id == evaluation_id,
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation project with ID '{evaluation_id}' not found",
        )

    # Check organisation access
    if evaluation.organisation_id not in org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this evaluation project",
        )

    return EvaluationResponse(
        id=evaluation.id,
        organisation_id=evaluation.organisation_id,
        created_by=evaluation.created_by,
        title=evaluation.title,
        target_url=evaluation.target_url,
        wcag_version=evaluation.wcag_version,
        conformance_level=evaluation.conformance_level,
        audit_type=evaluation.audit_type,
        status=evaluation.status,
        scope_config=evaluation.scope_config,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )


@router.patch("/{evaluation_id}", response_model=EvaluationResponse)
async def update_evaluation(
    evaluation_id: UUID,
    data: EvaluationUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """Update an evaluation project.

    Updates allowed fields of an evaluation project.
    Status cannot be changed directly - it is managed by the workflow.

    Syncs the updated evaluation to Firestore as a background task.

    Args:
        evaluation_id: UUID of the evaluation project
        data: Fields to update
        background_tasks: FastAPI BackgroundTasks for Firestore sync

    Returns:
        EvaluationResponse: Updated evaluation project

    Raises:
        HTTPException(404): If evaluation doesn't exist
        HTTPException(403): If user doesn't have access to the evaluation
    """
    org_ids = await _get_user_org_ids(user)

    # Fetch evaluation
    stmt = select(EvaluationProject).where(EvaluationProject.id == evaluation_id)
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation project with ID '{evaluation_id}' not found",
        )

    # Check organisation access
    if evaluation.organisation_id not in org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this evaluation project",
        )

    # Check if evaluation is deleted
    if evaluation.status == "DELETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a deleted evaluation project",
        )

    # Update allowed fields
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(evaluation, field):
            setattr(evaluation, field, value)

    await db.flush()

    # Build response
    response = EvaluationResponse(
        id=evaluation.id,
        organisation_id=evaluation.organisation_id,
        created_by=evaluation.created_by,
        title=evaluation.title,
        target_url=evaluation.target_url,
        wcag_version=evaluation.wcag_version,
        conformance_level=evaluation.conformance_level,
        audit_type=evaluation.audit_type,
        status=evaluation.status,
        scope_config=evaluation.scope_config,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )

    # Sync to Firestore as background task (fire-and-forget)
    evaluation_dict = {
        "id": evaluation.id,
        "organisation_id": evaluation.organisation_id,
        "created_by": evaluation.created_by,
        "title": evaluation.title,
        "target_url": evaluation.target_url,
        "wcag_version": evaluation.wcag_version,
        "conformance_level": evaluation.conformance_level,
        "audit_type": evaluation.audit_type,
        "status": evaluation.status,
        "created_at": evaluation.created_at,
        "updated_at": evaluation.updated_at,
    }
    background_tasks.add_task(sync_evaluation_to_firestore, evaluation_dict)

    return response


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an evaluation project (soft delete).

    Requires owner role in the evaluation's organisation.
    Sets the evaluation status to DELETED instead of hard delete.

    Deletes the evaluation from Firestore as a background task.

    Args:
        evaluation_id: UUID of the evaluation project
        background_tasks: FastAPI BackgroundTasks for Firestore sync

    Raises:
        HTTPException(404): If evaluation doesn't exist
        HTTPException(403): If user doesn't have owner access
    """
    # Fetch evaluation
    stmt = select(EvaluationProject).where(EvaluationProject.id == evaluation_id)
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation project with ID '{evaluation_id}' not found",
        )

    # Check if user has owner role in the evaluation's organisation
    user_role = None
    for role_entry in user.organisation_roles:
        if role_entry.organisation_id == evaluation.organisation_id:
            user_role = role_entry.role
            break

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this evaluation project",
        )

    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation owners can delete evaluation projects",
        )

    # Soft delete - set status to DELETED
    evaluation.status = "DELETED"
    await db.flush()

    # Delete from Firestore as background task (fire-and-forget)
    background_tasks.add_task(delete_evaluation_from_firestore, str(evaluation_id))
