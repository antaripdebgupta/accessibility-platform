"""
Disability Profile Engine.

Provides functions to apply disability profiles to findings:
- apply_profile_to_findings: Add profile-specific fields to findings
- filter_by_profile: Filter and sort findings by profile relevance
- get_profile_summary: Get statistics about findings for a profile
"""

from typing import Any

from profiles.definitions import get_profile, DisabilityProfile


# Priority ordering for sorting (lower number = higher priority)
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "na": 4,
}

# Severity ordering for sorting (lower number = higher severity)
SEVERITY_ORDER = {
    "critical": 0,
    "serious": 1,
    "moderate": 2,
    "minor": 3,
    "info": 4,
}


def apply_profile_to_findings(
    findings: list[dict[str, Any]],
    profile_id: str,
) -> list[dict[str, Any]]:
    """
    Apply a disability profile to a list of findings.

    Adds profile-specific fields to each finding:
    - profile_relevant: bool indicating if criterion matters for this profile
    - profile_priority: priority level for this profile (critical/high/medium/low/na)
    - profile_severity: boosted severity for this profile

    The original severity field is NEVER modified.

    Args:
        findings: List of finding dictionaries with criterion_code and severity
        profile_id: The profile ID to apply (e.g., "blind")

    Returns:
        List of findings with profile fields added. Returns unchanged if profile not found.
    """
    profile = get_profile(profile_id)
    if profile is None:
        return findings

    result = []
    for finding in findings:
        # Create a copy to avoid mutating the original
        enriched = dict(finding)

        # Get criterion code from finding
        criterion_code = finding.get("criterion_code")

        if criterion_code:
            # Look up priority for this criterion in the profile
            priority = profile.affected_criteria.get(criterion_code)

            if priority == "na":
                # Criterion is not applicable for this profile
                enriched["profile_relevant"] = False
                enriched["profile_priority"] = "na"
                # N/A findings keep their original severity, not boosted
                enriched["profile_severity"] = finding.get("severity")
            elif priority is not None:
                # Criterion has explicit priority for this profile
                enriched["profile_relevant"] = True
                enriched["profile_priority"] = priority
                # Apply severity boost
                original_severity = finding.get("severity") or "moderate"
                enriched["profile_severity"] = profile.boosted_severities.get(
                    original_severity, original_severity
                )
            else:
                # Criterion not in profile map, default to medium priority
                enriched["profile_relevant"] = True
                enriched["profile_priority"] = "medium"
                # Apply severity boost
                original_severity = finding.get("severity") or "moderate"
                enriched["profile_severity"] = profile.boosted_severities.get(
                    original_severity, original_severity
                )
        else:
            # No criterion code, default to relevant with medium priority
            enriched["profile_relevant"] = True
            enriched["profile_priority"] = "medium"
            original_severity = finding.get("severity") or "moderate"
            enriched["profile_severity"] = profile.boosted_severities.get(
                original_severity, original_severity
            )

        result.append(enriched)

    return result


def filter_by_profile(
    findings: list[dict[str, Any]],
    profile_id: str,
    exclude_na: bool = True,
) -> list[dict[str, Any]]:
    """
    Apply profile to findings, optionally filter out N/A findings, and sort by priority.

    Args:
        findings: List of finding dictionaries
        profile_id: The profile ID to apply
        exclude_na: If True, remove findings where profile_priority is "na"

    Returns:
        Filtered and sorted list of findings with profile fields added.
        Sorted by profile_priority (critical first) then by profile_severity.
    """
    # Apply profile to add fields
    enriched = apply_profile_to_findings(findings, profile_id)

    # Filter out N/A findings if requested
    if exclude_na:
        enriched = [f for f in enriched if f.get("profile_priority") != "na"]

    # Sort by priority then severity (critical/serious first)
    enriched.sort(
        key=lambda f: (
            PRIORITY_ORDER.get(f.get("profile_priority", "medium"), 2),
            SEVERITY_ORDER.get(f.get("profile_severity", "moderate"), 2),
        )
    )

    return enriched


def get_profile_summary(
    findings: list[dict[str, Any]],
    profile_id: str,
) -> dict[str, Any]:
    """
    Get summary statistics for findings from a profile perspective.

    Args:
        findings: List of finding dictionaries
        profile_id: The profile ID to analyze

    Returns:
        Dictionary with profile summary:
        - profile_id: The profile ID
        - profile_name: Human-readable profile name
        - critical_for_profile: Count of findings with critical priority
        - high_for_profile: Count of findings with high priority
        - not_applicable: Count of findings with na priority
        - total_relevant: Count of findings where priority != na
        - boosted_count: Count of findings where profile_severity != original severity
    """
    profile = get_profile(profile_id)
    if profile is None:
        return {
            "profile_id": profile_id,
            "profile_name": "Unknown Profile",
            "critical_for_profile": 0,
            "high_for_profile": 0,
            "not_applicable": 0,
            "total_relevant": 0,
            "boosted_count": 0,
        }

    # Apply profile to get priority and severity info
    enriched = apply_profile_to_findings(findings, profile_id)

    critical_count = 0
    high_count = 0
    na_count = 0
    boosted_count = 0

    for finding in enriched:
        priority = finding.get("profile_priority")
        original_severity = finding.get("severity")
        profile_severity = finding.get("profile_severity")

        if priority == "critical":
            critical_count += 1
        elif priority == "high":
            high_count += 1
        elif priority == "na":
            na_count += 1

        # Count boosted findings (severity increased, and not N/A)
        if priority != "na" and original_severity != profile_severity:
            boosted_count += 1

    total_relevant = len(enriched) - na_count

    return {
        "profile_id": profile_id,
        "profile_name": profile.name,
        "critical_for_profile": critical_count,
        "high_for_profile": high_count,
        "not_applicable": na_count,
        "total_relevant": total_relevant,
        "boosted_count": boosted_count,
    }


def get_all_profiles_summary(
    findings: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Get summary statistics for all profiles.

    Useful for reports that want to show all profile perspectives.

    Args:
        findings: List of finding dictionaries

    Returns:
        Dictionary mapping profile_id to profile summary
    """
    from profiles.definitions import PROFILES

    result = {}
    for profile_id in PROFILES:
        result[profile_id] = get_profile_summary(findings, profile_id)
    return result
