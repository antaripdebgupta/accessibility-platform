"""
Auth-related Pydantic schemas.

Schemas for user authentication responses including organisation memberships.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr


class OrgMembership(BaseModel):
    """Organisation membership with role.

    Attributes:
        id: Organisation UUID
        name: Organisation display name
        role: User's role in the organisation
    """

    id: UUID
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User profile response with organisation memberships.

    Attributes:
        id: User UUID
        email: User's email address
        display_name: Optional display name
        organisations: List of organisations the user belongs to
        current_organisation_id: Currently selected organisation UUID
        role: User's role in the current organisation
        permissions: List of permissions for the current organisation
    """

    id: UUID
    email: EmailStr
    display_name: Optional[str] = None
    organisations: List[OrgMembership] = []
    current_organisation_id: Optional[UUID] = None
    role: Optional[str] = None
    permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)
