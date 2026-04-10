"""
Disability Profiles API routes.

Provides endpoints for retrieving disability profile definitions.
Profiles are static reference data - no authentication required.
"""

from fastapi import APIRouter, HTTPException, status

from profiles.definitions import get_profile, list_profiles
from schemas.profile import ProfileListItem, ProfileListResponse, ProfileResponse

router = APIRouter(tags=["Profiles"])


@router.get(
    "",
    response_model=ProfileListResponse,
    summary="List all disability profiles",
    description="Returns a list of all available disability profiles with basic metadata. "
    "Does not include the full affected_criteria mapping to keep response size small.",
)
async def list_all_profiles() -> ProfileListResponse:
    """
    List all available disability profiles.

    Public endpoint - no authentication required.
    Returns basic profile info without the affected_criteria mapping.

    Returns:
        ProfileListResponse containing list of all profiles
    """
    profiles = list_profiles()

    items = [
        ProfileListItem(
            id=p.id,
            name=p.name,
            description=p.description,
            notes=p.notes,
        )
        for p in profiles
    ]

    return ProfileListResponse(profiles=items)


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get a disability profile by ID",
    description="Returns the full profile definition including the affected_criteria mapping "
    "which shows the priority level for each WCAG criterion from this profile's perspective.",
    responses={
        404: {"description": "Profile not found"},
    },
)
async def get_profile_detail(profile_id: str) -> ProfileResponse:
    """
    Get a single disability profile by ID.

    Public endpoint - no authentication required.
    Returns the full profile including affected_criteria mapping.

    Args:
        profile_id: Profile identifier (e.g., "blind", "low_vision", "motor", "cognitive")

    Returns:
        ProfileResponse with full profile details

    Raises:
        HTTPException: 404 if profile not found
    """
    profile = get_profile(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found. Valid profiles: blind, low_vision, motor, cognitive",
        )

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        notes=profile.notes,
        affected_criteria=profile.affected_criteria,
    )
