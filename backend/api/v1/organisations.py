"""
Organisation API routes.

Provides endpoints for organisation management:
- Create organisation
- List user's organisations
- Get organisation details
- Manage organisation members
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user
from db.session import get_db
from models.organisation import Organisation
from models.user import User
from models.user_org_role import UserOrganisationRole
from schemas.organisation import (
    MemberRoleUpdate,
    OrganisationCreate,
    OrganisationMember,
    OrganisationResponse,
    OrganisationWithRole,
)

router = APIRouter(tags=["Organisations"])


async def get_member_count(db: AsyncSession, org_id: UUID) -> int:
    """Get the number of members in an organisation."""
    count_stmt = (
        select(func.count())
        .select_from(UserOrganisationRole)
        .where(UserOrganisationRole.organisation_id == org_id)
    )
    result = await db.execute(count_stmt)
    return result.scalar() or 0


async def get_user_role_in_org(
    db: AsyncSession, user_id: UUID, org_id: UUID
) -> UserOrganisationRole | None:
    """Get user's role entry in an organisation, or None if not a member."""
    stmt = select(UserOrganisationRole).where(
        UserOrganisationRole.user_id == user_id,
        UserOrganisationRole.organisation_id == org_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def count_owners_in_org(db: AsyncSession, org_id: UUID) -> int:
    """Count the number of owners in an organisation."""
    stmt = (
        select(func.count())
        .select_from(UserOrganisationRole)
        .where(
            UserOrganisationRole.organisation_id == org_id,
            UserOrganisationRole.role == "owner",
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


@router.post("", response_model=OrganisationResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    data: OrganisationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganisationResponse:
    """Create a new organisation.

    The current user becomes the owner of the new organisation.

    Args:
        data: Organisation creation data (name, slug)

    Returns:
        OrganisationResponse with the created organisation details

    Raises:
        409: If slug is already taken
    """
    # Check if slug is unique
    slug_check = select(Organisation).where(Organisation.slug == data.slug)
    existing = await db.execute(slug_check)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An organisation with slug '{data.slug}' already exists",
        )

    # Create organisation
    organisation = Organisation(
        name=data.name,
        slug=data.slug,
    )
    db.add(organisation)
    await db.flush()

    # Add current user as owner
    user_role = UserOrganisationRole(
        user_id=user.id,
        organisation_id=organisation.id,
        role="owner",
    )
    db.add(user_role)
    await db.flush()

    return OrganisationResponse(
        id=organisation.id,
        name=organisation.name,
        slug=organisation.slug,
        created_at=organisation.created_at,
        member_count=1,
    )


@router.get("/me", response_model=List[OrganisationWithRole])
async def list_my_organisations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrganisationWithRole]:
    """List all organisations the current user belongs to.

    Returns organisations with the user's role and member count.

    Returns:
        List of OrganisationWithRole objects
    """
    # Fetch user's organisation roles with org details
    stmt = (
        select(UserOrganisationRole)
        .options(selectinload(UserOrganisationRole.organisation))
        .where(UserOrganisationRole.user_id == user.id)
        .order_by(UserOrganisationRole.created_at)
    )
    result = await db.execute(stmt)
    role_entries = result.scalars().all()

    organisations = []
    for role_entry in role_entries:
        org = role_entry.organisation
        member_count = await get_member_count(db, org.id)
        organisations.append(
            OrganisationWithRole(
                id=org.id,
                name=org.name,
                slug=org.slug,
                created_at=org.created_at,
                role=role_entry.role,
                member_count=member_count,
            )
        )

    return organisations


@router.get("/{org_id}", response_model=OrganisationResponse)
async def get_organisation(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganisationResponse:
    """Get organisation details.

    Requires the user to be a member of the organisation.

    Args:
        org_id: Organisation UUID

    Returns:
        OrganisationResponse with organisation details

    Raises:
        403: If user is not a member
        404: If organisation not found
    """
    # Check if user is a member
    user_role = await get_user_role_in_org(db, user.id, org_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organisation",
        )

    # Fetch organisation
    stmt = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found",
        )

    member_count = await get_member_count(db, org_id)

    return OrganisationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        member_count=member_count,
    )


@router.get("/{org_id}/members", response_model=List[OrganisationMember])
async def list_organisation_members(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrganisationMember]:
    """List all members of an organisation.

    Requires any membership role in the organisation.

    Args:
        org_id: Organisation UUID

    Returns:
        List of OrganisationMember objects

    Raises:
        403: If user is not a member
        404: If organisation not found
    """
    # Check if user is a member
    user_role = await get_user_role_in_org(db, user.id, org_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organisation",
        )

    # Verify organisation exists
    org_stmt = select(Organisation).where(Organisation.id == org_id)
    org_result = await db.execute(org_stmt)
    if not org_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found",
        )

    # Fetch all members
    stmt = (
        select(UserOrganisationRole)
        .options(selectinload(UserOrganisationRole.user))
        .where(UserOrganisationRole.organisation_id == org_id)
        .order_by(UserOrganisationRole.created_at)
    )
    result = await db.execute(stmt)
    role_entries = result.scalars().all()

    members = [
        OrganisationMember(
            user_id=entry.user.id,
            email=entry.user.email,
            display_name=entry.user.display_name,
            role=entry.role,
            joined_at=entry.created_at,
        )
        for entry in role_entries
    ]

    return members


@router.patch("/{org_id}/members/{user_id}", response_model=OrganisationMember)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    data: MemberRoleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganisationMember:
    """Update a member's role in the organisation.

    Requires owner role. Cannot change your own role.
    Cannot demote the last owner.

    Args:
        org_id: Organisation UUID
        user_id: User UUID to update
        data: New role data

    Returns:
        Updated OrganisationMember

    Raises:
        400: If trying to change own role or would leave org with no owners
        403: If user is not an owner
        404: If organisation or target user not found
    """
    # Check if current user is an owner
    current_user_role = await get_user_role_in_org(db, user.id, org_id)
    if not current_user_role or current_user_role.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation owners can change member roles",
        )

    # Cannot change own role
    if user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

    # Get target user's role entry
    target_role = await get_user_role_in_org(db, user_id, org_id)
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this organisation",
        )

    # Check if this would leave org with no owners
    if target_role.role == "owner" and data.role != "owner":
        owner_count = await count_owners_in_org(db, org_id)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last owner. Promote another member first.",
            )

    # Update the role
    target_role.role = data.role
    await db.flush()

    # Reload user for response
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one()

    return OrganisationMember(
        user_id=target_user.id,
        email=target_user.email,
        display_name=target_user.display_name,
        role=target_role.role,
        joined_at=target_role.created_at,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a member from the organisation.

    Requires owner role. Cannot remove yourself if you are the last owner.

    Args:
        org_id: Organisation UUID
        user_id: User UUID to remove

    Raises:
        400: If trying to remove self as last owner
        403: If user is not an owner
        404: If organisation or target user not found
    """
    # Check if current user is an owner
    current_user_role = await get_user_role_in_org(db, user.id, org_id)
    if not current_user_role or current_user_role.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation owners can remove members",
        )

    # Get target user's role entry
    target_role = await get_user_role_in_org(db, user_id, org_id)
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this organisation",
        )

    # Cannot remove self if last owner
    if user_id == user.id and target_role.role == "owner":
        owner_count = await count_owners_in_org(db, org_id)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself as the last owner. Transfer ownership first.",
            )

    # Check if removing another owner would leave org ownerless
    if target_role.role == "owner":
        owner_count = await count_owners_in_org(db, org_id)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner. Promote another member first.",
            )

    # Remove the member
    await db.delete(target_role)
    await db.flush()
