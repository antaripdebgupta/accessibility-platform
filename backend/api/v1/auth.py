"""
Auth API routes.

Provides endpoints for user authentication and profile management.
"""

from fastapi import APIRouter, Depends

from core.auth import AuthenticatedUser, get_current_user
from schemas.auth import OrgMembership, UserResponse

router = APIRouter(tags=["Auth"])


@router.post("/me", response_model=UserResponse)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user profile with organisation memberships.

    Returns the user's profile information including all organisations
    they belong to, their role in each organisation, and their
    permissions for the current organisation.

    Returns:
        UserResponse: User profile with organisation memberships and permissions
    """
    # Build list of organisation memberships
    organisations = [
        OrgMembership(
            id=role_entry.organisation.id,
            name=role_entry.organisation.name,
            role=role_entry.role,
        )
        for role_entry in user.organisation_roles
    ]

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        organisations=organisations,
        current_organisation_id=user.current_organisation_id,
        role=user.role,
        permissions=list(user.permissions),
    )
