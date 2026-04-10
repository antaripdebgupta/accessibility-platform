"""
Profile-related Pydantic schemas.

Schemas for disability profiles and profile-aware finding responses.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileSummary(BaseModel):
    """
    Summary statistics for findings from a profile perspective.

    Attributes:
        profile_id: Profile identifier (e.g., "blind")
        profile_name: Human-readable profile name
        critical_for_profile: Count of findings with critical priority for this profile
        high_for_profile: Count of findings with high priority for this profile
        not_applicable: Count of findings marked N/A for this profile
        total_relevant: Count of findings that are relevant (not N/A) for this profile
        boosted_count: Count of findings whose severity was boosted for this profile
    """

    profile_id: str
    profile_name: str
    critical_for_profile: int = 0
    high_for_profile: int = 0
    not_applicable: int = 0
    total_relevant: int = 0
    boosted_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProfileListItem(BaseModel):
    """
    Profile data for list endpoints (without affected_criteria).

    Attributes:
        id: Profile identifier
        name: Human-readable profile name
        description: Brief description of who this profile covers
        notes: Explanation of why these criteria matter
    """

    id: str
    name: str
    description: str
    notes: str

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    """
    Full profile data including affected_criteria mapping.

    Attributes:
        id: Profile identifier
        name: Human-readable profile name
        description: Brief description of who this profile covers
        notes: Explanation of why these criteria matter
        affected_criteria: Map of criterion_id to priority level
    """

    id: str
    name: str
    description: str
    notes: str
    affected_criteria: Optional[dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileListResponse(BaseModel):
    """
    Response containing list of all profiles.

    Attributes:
        profiles: List of profile summary items
    """

    profiles: list[ProfileListItem]

    model_config = ConfigDict(from_attributes=True)
