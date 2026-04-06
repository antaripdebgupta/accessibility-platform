"""
Invitation API routes.

Provides endpoints for the invitation system:
- Create invitations (owner only)
- List org invitations
- Revoke invitations
- Accept invitations (public)
- View invitation info (public)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth import get_current_user
from core.email import send_invitation_email
from core.firebase import verify_token
from db.session import get_db
from models.invitation import Invitation
from models.organisation import Organisation
from models.user import User
from models.user_org_role import UserOrganisationRole
from schemas.organisation import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    InvitationCreate,
    InvitationPublicInfo,
    InvitationResponse,
)

router = APIRouter(tags=["Invitations"])
optional_security = HTTPBearer(auto_error=False)


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


async def require_owner(
    org_id: UUID,
    user: User,
    db: AsyncSession,
) -> None:
    """Verify user is an owner of the organisation."""
    user_role = await get_user_role_in_org(db, user.id, org_id)
    if not user_role or user_role.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation owners can manage invitations",
        )


async def get_organisation_or_404(db: AsyncSession, org_id: UUID) -> Organisation:
    """Fetch organisation by ID or raise 404."""
    stmt = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found",
        )
    return org


@router.post(
    "/organisations/{org_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    org_id: UUID,
    data: InvitationCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Create a new invitation to join the organisation.

    Requires owner role. Sends invitation email via background task.

    Args:
        org_id: Organisation UUID
        data: Invitation data (email, role)
        background_tasks: For async email sending

    Returns:
        InvitationResponse with created invitation details

    Raises:
        403: If user is not an owner
        404: If organisation not found
        409: If user already in org or pending invitation exists
    """
    await require_owner(org_id, user, db)
    org = await get_organisation_or_404(db, org_id)

    email_lower = data.email.lower()

    # Check if user already exists and is a member
    existing_user_stmt = select(User).where(User.email == email_lower)
    existing_user_result = await db.execute(existing_user_stmt)
    existing_user = existing_user_result.scalar_one_or_none()

    if existing_user:
        existing_membership = await get_user_role_in_org(db, existing_user.id, org_id)
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{data.email}' is already a member of this organisation",
            )

    # Check for pending invitation
    pending_stmt = select(Invitation).where(
        and_(
            Invitation.organisation_id == org_id,
            Invitation.email == email_lower,
            Invitation.status == "pending",
        )
    )
    pending_result = await db.execute(pending_stmt)
    if pending_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A pending invitation already exists for '{data.email}'",
        )

    # Create invitation
    invitation = Invitation(
        organisation_id=org_id,
        invited_by=user.id,
        email=email_lower,
        role=data.role,
    )
    db.add(invitation)
    await db.flush()

    # Send invitation email as background task
    inviter_name = user.display_name or user.email
    background_tasks.add_task(
        send_invitation_email,
        to_email=email_lower,
        invited_by=inviter_name,
        org_name=org.name,
        role=data.role,
        token=str(invitation.token),
    )

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invited_by_email=user.email,
        created_at=invitation.created_at,
    )


@router.get(
    "/organisations/{org_id}/invitations",
    response_model=List[InvitationResponse],
)
async def list_invitations(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[InvitationResponse]:
    """List all invitations for an organisation.

    Requires owner role.

    Args:
        org_id: Organisation UUID

    Returns:
        List of InvitationResponse objects

    Raises:
        403: If user is not an owner
        404: If organisation not found
    """
    await require_owner(org_id, user, db)
    await get_organisation_or_404(db, org_id)

    stmt = (
        select(Invitation)
        .options(selectinload(Invitation.inviter))
        .where(Invitation.organisation_id == org_id)
        .order_by(Invitation.created_at.desc())
    )
    result = await db.execute(stmt)
    invitations = result.scalars().all()

    return [
        InvitationResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at,
            invited_by_email=inv.inviter.email if inv.inviter else None,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


@router.delete(
    "/organisations/{org_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invitation(
    org_id: UUID,
    invitation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a pending invitation.

    Requires owner role. Sets invitation status to 'revoked'.

    Args:
        org_id: Organisation UUID
        invitation_id: Invitation UUID to revoke

    Raises:
        403: If user is not an owner
        404: If organisation or invitation not found
    """
    await require_owner(org_id, user, db)
    await get_organisation_or_404(db, org_id)

    stmt = select(Invitation).where(
        and_(
            Invitation.id == invitation_id,
            Invitation.organisation_id == org_id,
        )
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    invitation.status = "revoked"
    await db.flush()


@router.post("/invitations/{token}/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    token: UUID,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
) -> AcceptInvitationResponse:
    """Accept an invitation to join an organisation.

    Requires a valid Firebase token to identify the accepting user.

    Args:
        token: Invitation token UUID (in path)

    Returns:
        AcceptInvitationResponse with organisation info

    Raises:
        400: If invitation already used, expired, or revoked
        401: If no valid Firebase token provided
        404: If invitation token not found
    """
    # Require Firebase token for accepting invitations
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to accept an invitation",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    firebase_uid = claims.get("uid")
    email = claims.get("email")
    display_name = claims.get("name")

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find invitation by token
    stmt = (
        select(Invitation)
        .options(selectinload(Invitation.organisation))
        .where(Invitation.token == token)
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Check invitation status
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This invitation has already been {invitation.status}",
        )

    # Check expiration
    now = datetime.utcnow()
    expires_at_naive = invitation.expires_at.replace(tzinfo=None) if invitation.expires_at.tzinfo else invitation.expires_at
    if now > expires_at_naive:
        invitation.status = "expired"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired",
        )

    # Get or create user
    user_stmt = select(User).where(User.firebase_uid == firebase_uid)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        # Check if user exists with same email but different firebase_uid
        email_stmt = select(User).where(User.email == email)
        email_result = await db.execute(email_stmt)
        user = email_result.scalar_one_or_none()

        if user:
            # Link existing user to this Firebase UID
            user.firebase_uid = firebase_uid
            user.last_login_at = now
        else:
            # Create new user
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name,
                last_login_at=now,
            )
            db.add(user)
        await db.flush()

    # Check if user is already a member
    existing_membership = await get_user_role_in_org(db, user.id, invitation.organisation_id)
    if existing_membership:
        # User already in org, just mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = now
        await db.flush()
        return AcceptInvitationResponse(
            organisation_id=invitation.organisation_id,
            organisation_name=invitation.organisation.name,
            role=existing_membership.role,
            message="You are already a member of this organisation",
        )

    # Add user to organisation with invited role
    user_role = UserOrganisationRole(
        user_id=user.id,
        organisation_id=invitation.organisation_id,
        role=invitation.role,
    )
    db.add(user_role)

    # Mark invitation as accepted
    invitation.status = "accepted"
    invitation.accepted_at = now
    await db.flush()

    return AcceptInvitationResponse(
        organisation_id=invitation.organisation_id,
        organisation_name=invitation.organisation.name,
        role=invitation.role,
        message=f"Successfully joined {invitation.organisation.name} as {invitation.role}",
    )


@router.get("/invitations/{token}", response_model=InvitationPublicInfo)
async def get_invitation_info(
    token: UUID,
    db: AsyncSession = Depends(get_db),
) -> InvitationPublicInfo:
    """Get public information about an invitation.

    This is a public route for the frontend to display invitation details
    before the user logs in.

    Args:
        token: Invitation token UUID

    Returns:
        InvitationPublicInfo without internal IDs

    Raises:
        404: If invitation not found
    """
    stmt = (
        select(Invitation)
        .options(
            selectinload(Invitation.organisation),
            selectinload(Invitation.inviter),
        )
        .where(Invitation.token == token)
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Update status if expired but still marked pending
    now = datetime.utcnow()
    expires_at_naive = invitation.expires_at.replace(tzinfo=None) if invitation.expires_at.tzinfo else invitation.expires_at
    current_status = invitation.status
    if current_status == "pending" and now > expires_at_naive:
        invitation.status = "expired"
        current_status = "expired"
        await db.flush()

    inviter_display = "Unknown"
    if invitation.inviter:
        inviter_display = invitation.inviter.display_name or invitation.inviter.email

    return InvitationPublicInfo(
        organisation_id=invitation.organisation_id,
        organisation_name=invitation.organisation.name,
        email=invitation.email,
        invited_by=inviter_display,
        role=invitation.role,
        expires_at=invitation.expires_at,
        status=current_status,
    )
