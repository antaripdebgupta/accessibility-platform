"""
Disability Profile Definitions.

Contains the static profile data for all supported disability profiles.
Each profile defines:
- affected_criteria: WCAG criterion → priority mapping
- boosted_severities: original severity → boosted severity for this profile
- Metadata (name, description, icon, notes)

Priority levels:
- critical: Blocks access entirely for this user group
- high: Significant barrier for this user group
- medium: Moderate barrier
- low: Minor barrier
- na: Not applicable (visual criteria for blind users, etc.)
"""

from dataclasses import dataclass, field


@dataclass
class DisabilityProfile:
    """
    Represents a disability user profile with WCAG criteria priority mapping.

    Attributes:
        id: Profile identifier (e.g., "blind", "low_vision")
        name: Human-readable profile name
        description: Brief description of who this profile covers
        affected_criteria: Map of criterion_id to priority level
        boosted_severities: Map of original severity to boosted severity
        notes: Explanation of why these criteria matter for this profile
    """

    id: str
    name: str
    description: str
    affected_criteria: dict[str, str] = field(default_factory=dict)
    boosted_severities: dict[str, str] = field(default_factory=dict)
    notes: str = ""


# All supported disability profiles
PROFILES: dict[str, DisabilityProfile] = {
    "blind": DisabilityProfile(
        id="blind",
        name="Blind / Screen Reader Users",
        description="Users who are blind and navigate using screen readers such as NVDA, JAWS, or VoiceOver.",
        notes="Screen reader users rely on text alternatives, semantic structure, and programmatic labels. Visual-only criteria such as colour contrast are not applicable.",
        affected_criteria={
            # Critical — blocks screen reader access entirely
            "1.1.1": "critical",  # Non-text Content — alt text
            "1.3.1": "critical",  # Info and Relationships — semantic structure
            "1.3.2": "critical",  # Meaningful Sequence
            "2.4.1": "critical",  # Bypass Blocks
            "2.4.2": "critical",  # Page Titled
            "2.4.4": "critical",  # Link Purpose
            "2.4.6": "critical",  # Headings and Labels
            "4.1.1": "critical",  # Parsing
            "4.1.2": "critical",  # Name Role Value
            "4.1.3": "critical",  # Status Messages
            # High — significant barrier
            "1.2.1": "high",  # Audio-only and Video-only
            "1.2.2": "high",  # Captions (Prerecorded)
            "1.2.3": "high",  # Audio Description
            "2.1.1": "high",  # Keyboard
            "2.4.3": "high",  # Focus Order
            "3.3.1": "high",  # Error Identification
            "3.3.2": "high",  # Labels or Instructions
            # Medium
            "2.4.5": "medium",  # Multiple Ways
            "3.1.1": "medium",  # Language of Page
            "3.2.1": "medium",  # On Focus
            "3.2.2": "medium",  # On Input
            "3.3.3": "medium",  # Error Suggestion
            "3.3.4": "medium",  # Error Prevention
            # Not applicable — visual criteria
            "1.4.1": "na",  # Use of Colour
            "1.4.3": "na",  # Contrast (Minimum)
            "1.4.4": "na",  # Resize Text
            "1.4.6": "na",  # Contrast (Enhanced)
            "1.4.10": "na",  # Reflow
            "1.4.11": "na",  # Non-text Contrast
            "1.4.12": "na",  # Text Spacing
        },
        boosted_severities={
            "minor": "moderate",
            "moderate": "serious",
            "serious": "critical",
            "critical": "critical",
        },
    ),
    "low_vision": DisabilityProfile(
        id="low_vision",
        name="Low Vision Users",
        description="Users with partial sight who use screen magnification, high contrast modes, or large text settings.",
        notes="Low vision users depend on sufficient colour contrast, text scalability, and content reflow at high zoom levels.",
        affected_criteria={
            "1.4.3": "critical",  # Contrast (Minimum)
            "1.4.4": "critical",  # Resize Text
            "1.4.10": "critical",  # Reflow
            "1.4.11": "critical",  # Non-text Contrast
            "1.4.12": "critical",  # Text Spacing
            "1.4.6": "high",  # Contrast (Enhanced)
            "1.4.1": "high",  # Use of Colour
            "1.3.4": "high",  # Orientation
            "2.4.6": "high",  # Headings and Labels
            "1.1.1": "medium",  # Non-text Content
            "2.4.3": "medium",  # Focus Order
            "2.4.4": "medium",  # Link Purpose
            "1.4.5": "medium",  # Images of Text
            "4.1.2": "medium",  # Name Role Value
            "2.1.1": "low",  # Keyboard
            "1.3.1": "low",  # Info and Relationships
        },
        boosted_severities={
            "minor": "moderate",
            "moderate": "serious",
            "serious": "critical",
            "critical": "critical",
        },
    ),
    "motor": DisabilityProfile(
        id="motor",
        name="Motor Impaired Users",
        description="Users with limited motor control who navigate using keyboards, switch access, eye tracking, or voice control instead of a mouse.",
        notes="Motor impaired users require full keyboard operability, visible focus indicators, sufficient click target sizes, and no time limits on interactions.",
        affected_criteria={
            "2.1.1": "critical",  # Keyboard
            "2.1.2": "critical",  # No Keyboard Trap
            "2.4.3": "critical",  # Focus Order
            "2.4.7": "critical",  # Focus Visible
            "2.5.1": "critical",  # Pointer Gestures
            "2.5.2": "critical",  # Pointer Cancellation
            "2.5.3": "critical",  # Label in Name
            "2.5.4": "critical",  # Motion Actuation
            "2.1.4": "high",  # Character Key Shortcuts
            "2.2.1": "high",  # Timing Adjustable
            "2.2.2": "high",  # Pause Stop Hide
            "2.4.1": "high",  # Bypass Blocks
            "3.2.1": "high",  # On Focus
            "3.2.2": "high",  # On Input
            "3.3.2": "high",  # Labels or Instructions
            "4.1.2": "medium",  # Name Role Value
            "2.4.4": "medium",  # Link Purpose
            "3.3.1": "medium",  # Error Identification
            "3.3.4": "medium",  # Error Prevention
            "1.4.3": "low",  # Contrast
            "1.1.1": "low",  # Alt text
        },
        boosted_severities={
            "minor": "moderate",
            "moderate": "serious",
            "serious": "critical",
            "critical": "critical",
        },
    ),
    "cognitive": DisabilityProfile(
        id="cognitive",
        name="Cognitive & Learning Disabilities",
        description="Users with dyslexia, ADHD, memory difficulties, or other cognitive differences who need clear language, consistent layouts, and forgiving error handling.",
        notes="Cognitive users benefit from plain language, predictable navigation, clear error messages, and avoiding distracting animations or time pressure.",
        affected_criteria={
            "3.1.1": "critical",  # Language of Page
            "3.1.2": "critical",  # Language of Parts
            "3.2.3": "critical",  # Consistent Navigation
            "3.2.4": "critical",  # Consistent Identification
            "3.3.1": "critical",  # Error Identification
            "3.3.2": "critical",  # Labels or Instructions
            "3.3.3": "critical",  # Error Suggestion
            "3.3.4": "critical",  # Error Prevention
            "2.4.2": "high",  # Page Titled
            "2.4.6": "high",  # Headings and Labels
            "2.2.1": "high",  # Timing Adjustable
            "2.2.2": "high",  # Pause Stop Hide
            "1.4.8": "high",  # Visual Presentation
            "2.4.4": "medium",  # Link Purpose
            "2.4.5": "medium",  # Multiple Ways
            "3.2.1": "medium",  # On Focus
            "3.2.2": "medium",  # On Input
            "1.3.1": "medium",  # Info and Relationships
            "2.1.1": "low",  # Keyboard
            "1.4.3": "low",  # Contrast
            "1.1.1": "low",  # Alt text
            "2.3.1": "high",  # Three Flashes
        },
        boosted_severities={
            "minor": "minor",
            "moderate": "serious",
            "serious": "critical",
            "critical": "critical",
        },
    ),
}


def get_profile(profile_id: str) -> DisabilityProfile | None:
    """
    Get a disability profile by its ID.

    Args:
        profile_id: The profile identifier (e.g., "blind", "low_vision")

    Returns:
        The DisabilityProfile if found, None otherwise
    """
    return PROFILES.get(profile_id)


def list_profiles() -> list[DisabilityProfile]:
    """
    Get a list of all available disability profiles.

    Returns:
        List of all DisabilityProfile objects
    """
    return list(PROFILES.values())
