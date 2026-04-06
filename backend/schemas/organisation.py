"""
Organisation-related Pydantic schemas.

Schemas for organisation management, membership, and invitations.
"""

import re
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class OrganisationCreate(BaseModel):
    """Schema for creating a new organisation.

    Attributes:
        name: Organisation display name (2-80 characters)
        slug: URL-friendly identifier (lowercase alphanumeric + hyphens, 2-40 chars)
    """

    name: str
    slug: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate organisation name."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Organisation name must be at least 2 characters")
        if len(v) > 80:
            raise ValueError("Organisation name must be 80 characters or less")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase alphanumeric and hyphens only."""
        v = v.strip().lower()
        if len(v) < 2:
            raise ValueError("Slug must be at least 2 characters")
        if len(v) > 40:
            raise ValueError("Slug must be 40 characters or less")
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens, "
                "and cannot start or end with a hyphen"
            )
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v

    model_config = ConfigDict(from_attributes=True)


class OrganisationResponse(BaseModel):
    """Response schema for organisation details.

    Attributes:
        id: Organisation UUID
        name: Organisation display name
        slug: URL-friendly identifier
        created_at: When the organisation was created
        member_count: Number of members in the organisation
    """

    id: UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int

    model_config = ConfigDict(from_attributes=True)


class OrganisationWithRole(BaseModel):
    """Organisation with the current user's role.

    Attributes:
        id: Organisation UUID
        name: Organisation display name
        slug: URL-friendly identifier
        created_at: When the organisation was created
        role: User's role in this organisation
        member_count: Number of members in the organisation
    """

    id: UUID
    name: str
    slug: str
    created_at: datetime
    role: str
    member_count: int

    model_config = ConfigDict(from_attributes=True)


class OrganisationMember(BaseModel):
    """Schema for organisation member details.

    Attributes:
        user_id: User UUID
        email: User's email address
        display_name: User's display name (if set)
        role: User's role in the organisation
        joined_at: When the user joined the organisation
    """

    user_id: UUID
    email: str
    display_name: Optional[str] = None
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberRoleUpdate(BaseModel):
    """Schema for updating a member's role.

    Attributes:
        role: New role to assign (owner, auditor, reviewer, or viewer)
    """

    role: Literal["owner", "auditor", "reviewer", "viewer"]

    model_config = ConfigDict(from_attributes=True)


class InvitationCreate(BaseModel):
    """Schema for creating an invitation.

    Attributes:
        email: Email address to invite
        role: Role to assign (auditor, reviewer, or viewer - not owner)
    """

    email: EmailStr
    role: Literal["auditor", "reviewer", "viewer"]

    model_config = ConfigDict(from_attributes=True)


class InvitationResponse(BaseModel):
    """Response schema for invitation details.

    Attributes:
        id: Invitation UUID
        email: Invited email address
        role: Role to be assigned
        status: Current status (pending, accepted, expired, revoked)
        expires_at: When the invitation expires
        invited_by_email: Email of the user who sent the invitation
        created_at: When the invitation was created
    """

    id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    invited_by_email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AcceptInvitationRequest(BaseModel):
    """Request schema for accepting an invitation.

    Attributes:
        token: Invitation token UUID
    """

    token: UUID

    model_config = ConfigDict(from_attributes=True)


class AcceptInvitationResponse(BaseModel):
    """Response schema for successful invitation acceptance.

    Attributes:
        organisation_id: UUID of the organisation joined
        organisation_name: Name of the organisation joined
        role: Role assigned to the user
        message: Success message
    """

    organisation_id: UUID
    organisation_name: str
    role: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class InvitationPublicInfo(BaseModel):
    """Public invitation info for unauthenticated users.

    Does not expose internal UUIDs except for display purposes.

    Attributes:
        organisation_id: Organisation UUID (needed for post-accept redirect)
        organisation_name: Name of the organisation
        email: Email the invitation was sent to
        invited_by: Display name or email of inviter
        role: Role to be assigned
        expires_at: When the invitation expires
        status: Current invitation status
    """

    organisation_id: UUID
    organisation_name: str
    email: str
    invited_by: str
    role: str
    expires_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)
