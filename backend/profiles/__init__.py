"""
Disability Profiles Module.

Provides disability profile definitions and profile-aware severity mapping
for accessibility findings. Supports 4 profiles:
- Blind / Screen Reader Users
- Low Vision Users
- Motor Impaired Users
- Cognitive & Learning Disabilities

Each profile defines which WCAG criteria are critical, high, medium, low,
or not applicable (na) for that user group, and how severities should be
boosted when viewing findings from that perspective.
"""

from profiles.definitions import (
    DisabilityProfile,
    PROFILES,
    get_profile,
    list_profiles,
)
from profiles.engine import (
    apply_profile_to_findings,
    filter_by_profile,
    get_profile_summary,
)

__all__ = [
    "DisabilityProfile",
    "PROFILES",
    "get_profile",
    "list_profiles",
    "apply_profile_to_findings",
    "filter_by_profile",
    "get_profile_summary",
]
