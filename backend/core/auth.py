"""FastAPI dependencies for Firebase authenticated routes.

Provides dependencies for:
- get_current_user: Verifies Bearer token and returns/creates User ORM object
- get_current_org: Returns user, organisation, and role for evaluation routes
- require_role: Role-based access control dependency factory
- require_permission: Permission-based access control dependency factory
"""

from datetime import datetime
from typing import Optional, Tuple, Set
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.firebase import verify_token
from core.permissions import Role, can, get_permissions_for_role
from db.session import get_db
from db.rls import set_rls_context
from models.user import User
from models.user_org_role import UserOrganisationRole
from models.organisation import Organisation
from models.evaluation import EvaluationProject

security = HTTPBearer()


class AuthenticatedUser:
    """
    Wrapper class for authenticated user with role and permissions.

    This class wraps the User ORM object and adds:
    - current_organisation_id: The active organisation ID
    - role: The user's role in the current organisation
    - permissions: Set of action strings the user can perform
    """

    def __init__(
        self,
        user: User,
        current_organisation_id: Optional[UUID] = None,
        role: Optional[str] = None,
    ):
        self._user = user
        self.current_organisation_id = current_organisation_id
        self.role = role
        self._permissions: Optional[Set[str]] = None

    @property
    def permissions(self) -> Set[str]:
        """Get the set of permissions for this user's role."""
        if self._permissions is None:
            if self.role:
                self._permissions = get_permissions_for_role(self.role)
            else:
                self._permissions = set()
        return self._permissions

    def can(self, action: str) -> bool:
        """Check if the user can perform the given action."""
        return action in self.permissions

    # Proxy all User attributes
    def __getattr__(self, name):
        return getattr(self._user, name)

    @property
    def id(self):
        return self._user.id

    @property
    def email(self):
        return self._user.email

    @property
    def display_name(self):
        return self._user.display_name

    @property
    def firebase_uid(self):
        return self._user.firebase_uid

    @property
    def organisation_roles(self):
        return self._user.organisation_roles

    @property
    def last_login_at(self):
        return self._user.last_login_at


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    x_organisation_id: Optional[str] = Header(None, alias="X-Organisation-ID"),
) -> AuthenticatedUser:
    """Extract and verify the bearer token and return AuthenticatedUser.

    If the user doesn't exist in the database (first login), creates a new user record.
    Updates last_login_at timestamp on each authentication.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Async database session
        x_organisation_id: Optional header to specify active organisation

    Returns:
        AuthenticatedUser object with user data, role, and permissions

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

    # Determine the current organisation and user's role
    current_org_id: Optional[UUID] = None
    current_role: Optional[str] = None

    try:
        if user.organisation_roles:
            if x_organisation_id:
                try:
                    org_uuid = UUID(x_organisation_id)
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid X-Organisation-ID format. Must be a valid UUID.",
                    )

                # Verify membership and get role
                for r in user.organisation_roles:
                    if r.organisation_id == org_uuid:
                        current_org_id = org_uuid
                        current_role = r.role
                        break

                if current_org_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not a member of this organisation",
                    )
            else:
                # Fall back to first organisation
                first_role = user.organisation_roles[0]
                current_org_id = first_role.organisation_id
                current_role = first_role.role

            # Set RLS context
            if current_org_id:
                await set_rls_context(db, str(user.id), str(current_org_id))

    except HTTPException:
        # re-raise permission/validation errors
        raise
    except Exception:
        # Any failures setting RLS context are fatal for security
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialise request security context",
        )

    return AuthenticatedUser(
        user=user,
        current_organisation_id=current_org_id,
        role=current_role,
    )


async def get_current_org(
    evaluation_id: UUID = Path(..., description="Evaluation project ID"),
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[AuthenticatedUser, Organisation, str]:
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
    the allowed roles in their current organisation.

    Usage:
        @router.delete("/resource/{id}")
        async def delete_resource(
            user: AuthenticatedUser = Depends(require_role("owner")),
            ...
        ):
            ...

    Args:
        *allowed_roles: Role names that are permitted (e.g., "owner", "auditor")

    Returns:
        FastAPI dependency function
    """
    # Convert string roles to Role enum values for comparison
    allowed_role_enums = set()
    for role_str in allowed_roles:
        try:
            allowed_role_enums.add(Role(role_str))
        except ValueError:
            # Invalid role string, skip
            pass

    async def check_role(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        """Check if the user has one of the allowed roles."""
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organisation context. Please select an organisation.",
            )

        try:
            user_role = Role(current_user.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid role: {current_user.role}",
            )

        if user_role not in allowed_role_enums:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. This action requires one of the following roles: {', '.join(allowed_roles)}",
            )

        return current_user

    return check_role


def require_permission(action: str):
    """
    Dependency factory for permission-based access control.

    Creates a FastAPI dependency that checks if the current user has
    permission to perform the specified action based on their role.

    Usage:
        @router.post("/evaluations")
        async def create_evaluation(
            user: AuthenticatedUser = Depends(require_permission("evaluation.create")),
            ...
        ):
            ...

    Args:
        action: The action string to check (e.g., "evaluation.create")

    Returns:
        FastAPI dependency function
    """
    async def check_permission(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        """Check if the user has permission to perform the action."""
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organisation context. Please select an organisation.",
            )

        if not can(current_user.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted to perform '{action}'",
            )

        return current_user

    return check_permission


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
            user: AuthenticatedUser = Depends(require_org_role("owner", "auditor", "reviewer")),
            ...
        ):
            ...

    Args:
        *allowed_roles: Role names that are permitted

    Returns:
        FastAPI dependency function that returns (AuthenticatedUser, Organisation, role)
    """
    # Convert string roles to Role enum values for comparison
    allowed_role_enums = set()
    for role_str in allowed_roles:
        try:
            allowed_role_enums.add(Role(role_str))
        except ValueError:
            pass

    async def check_org_role(
        evaluation_id: UUID = Path(..., description="Evaluation project ID"),
        current_user: AuthenticatedUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Tuple[AuthenticatedUser, Organisation, str]:
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
        try:
            user_role_enum = Role(org_role.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid role: {org_role.role}",
            )

        if user_role_enum not in allowed_role_enums:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. This action requires one of the following roles: {', '.join(allowed_roles)}",
            )

        return current_user, evaluation.organisation, org_role.role

    return check_org_role
