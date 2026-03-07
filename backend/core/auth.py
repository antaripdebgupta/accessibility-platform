"""FastAPI dependencies for Firebase authenticated routes.

Provides dependencies for:
- get_current_user: Verifies Bearer token and returns/creates User ORM object
- get_current_org: Returns user, organisation, and role for evaluation routes
"""

from datetime import datetime
from typing import Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.firebase import verify_token
from db.session import get_db
from models.user import User
from models.user_org_role import UserOrganisationRole
from models.organisation import Organisation
from models.evaluation import EvaluationProject

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify the bearer token and return User ORM object.

    If the user doesn't exist in the database (first login), creates a new user record.
    Updates last_login_at timestamp on each authentication.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Async database session

    Returns:
        User ORM object with organisation_roles eagerly loaded

    Raises:
        HTTPException(401): If token is missing, invalid, or expired
    """
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_token(token)
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
            detail="Invalid token claims: missing uid or email",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user by firebase_uid with organisation roles eagerly loaded
    stmt = (
        select(User)
        .options(selectinload(User.organisation_roles).selectinload(UserOrganisationRole.organisation))
        .where(User.firebase_uid == firebase_uid)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        # Check if user exists with same email but different firebase_uid
        email_stmt = select(User).where(User.email == email)
        email_result = await db.execute(email_stmt)
        existing_user = email_result.scalar_one_or_none()

        if existing_user:
            # Update firebase_uid for existing user
            existing_user.firebase_uid = firebase_uid
            existing_user.last_login_at = datetime.utcnow()
            await db.flush()

            # Reload with relationships
            stmt = (
                select(User)
                .options(selectinload(User.organisation_roles).selectinload(UserOrganisationRole.organisation))
                .where(User.id == existing_user.id)
            )
            result = await db.execute(stmt)
            user = result.scalar_one()
        else:
            # First login - create user and assign to default org
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
            await db.flush()

            # Get or create default organisation
            default_org_id = UUID('00000000-0000-0000-0000-000000000001')
            org_stmt = select(Organisation).where(Organisation.id == default_org_id)
            org_result = await db.execute(org_stmt)
            org = org_result.scalar_one_or_none()

            if not org:
                org = Organisation(id=default_org_id, name='Default Organisation', slug='default')
                db.add(org)
                await db.flush()

            # Assign user to default org as owner
            user_org_role = UserOrganisationRole(
                user_id=user.id,
                organisation_id=default_org_id,
                role='owner'
            )
            db.add(user_org_role)
            await db.flush()

            # Reload with relationships
            stmt = (
                select(User)
                .options(selectinload(User.organisation_roles).selectinload(UserOrganisationRole.organisation))
                .where(User.id == user.id)
            )
            result = await db.execute(stmt)
            user = result.scalar_one()
    else:
        # Update last login time
        user.last_login_at = datetime.utcnow()
        await db.flush()

    return user


async def get_current_org(
    evaluation_id: UUID = Path(..., description="Evaluation project ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[User, Organisation, str]:
    """Get user, organisation, and role for an evaluation project.

    Verifies that the user has access to the evaluation's organisation.

    Args:
        evaluation_id: UUID of the evaluation project
        user: Current authenticated user
        db: Async database session

    Returns:
        Tuple of (User, Organisation, role string)

    Raises:
        HTTPException(404): If evaluation doesn't exist
        HTTPException(403): If user is not a member of the evaluation's organisation
    """
    # Fetch the evaluation project
    stmt = (
        select(EvaluationProject)
        .options(selectinload(EvaluationProject.organisation))
        .where(EvaluationProject.id == evaluation_id)
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation project with ID '{evaluation_id}' not found",
        )

    # Check if user is a member of the evaluation's organisation
    org_role = None
    for role_entry in user.organisation_roles:
        if role_entry.organisation_id == evaluation.organisation_id:
            org_role = role_entry
            break

    if org_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this evaluation project",
        )

    return user, evaluation.organisation, org_role.role


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.

    Creates a FastAPI dependency that checks if the current user has one of
    the allowed roles in any of their organisations.

    Usage:
        @router.delete("/resource/{id}")
        async def delete_resource(
            user: User = Depends(require_role("owner")),
            ...
        ):
            ...

        @router.post("/resource")
        async def create_resource(
            user: User = Depends(require_role("owner", "auditor")),
            ...
        ):
            ...

    Args:
        *allowed_roles: Role names that are permitted (e.g., "owner", "auditor", "reviewer", "viewer")

    Returns:
        FastAPI dependency function
    """
    async def check_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """Check if the user has one of the allowed roles."""
        # Check if user has any of the required roles in any organisation
        for role_entry in current_user.organisation_roles:
            if role_entry.role in allowed_roles:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. This action requires one of the following roles: {', '.join(allowed_roles)}",
        )

    return check_role


def require_org_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control scoped to an evaluation's organisation.

    Similar to require_role, but checks the user's role specifically in the
    organisation that owns the evaluation being accessed.

    Usage:
        @router.patch("/evaluations/{evaluation_id}/findings/{finding_id}")
        async def update_finding(
            evaluation_id: UUID,
            finding_id: UUID,
            user: User = Depends(require_org_role("owner", "auditor", "reviewer")),
            ...
        ):
            ...

    Args:
        *allowed_roles: Role names that are permitted

    Returns:
        FastAPI dependency function that returns (User, Organisation, role)
    """
    async def check_org_role(
        evaluation_id: UUID = Path(..., description="Evaluation project ID"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Tuple[User, Organisation, str]:
        """Check if the user has one of the allowed roles in the evaluation's organisation."""
        # Fetch the evaluation project
        stmt = (
            select(EvaluationProject)
            .options(selectinload(EvaluationProject.organisation))
            .where(EvaluationProject.id == evaluation_id)
        )
        result = await db.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if evaluation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation project with ID '{evaluation_id}' not found",
            )

        # Check if user is a member of the evaluation's organisation
        org_role = None
        for role_entry in current_user.organisation_roles:
            if role_entry.organisation_id == evaluation.organisation_id:
                org_role = role_entry
                break

        if org_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this evaluation project",
            )

        # Check if user's role is in the allowed roles
        if org_role.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. This action requires one of the following roles: {', '.join(allowed_roles)}",
            )

        return current_user, evaluation.organisation, org_role.role

    return check_org_role

