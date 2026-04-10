"""
Finding-related Pydantic schemas.

Schemas for accessibility findings within an evaluation project.
Findings can come from automated tools (axe-core, pa11y) or manual review.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from schemas.common import PaginatedResponse


class FindingResponse(BaseModel):
    """Schema for finding response.

    Represents an accessibility issue found during evaluation.

    Attributes:
        id: Finding UUID
        evaluation_id: Parent evaluation UUID
        page_id: Page where the issue was found
        criterion_id: WCAG criterion UUID (optional)
        criterion_code: WCAG criterion code like "1.1.1" (optional)
        criterion_name: WCAG criterion name (optional)
        criterion_level: WCAG conformance level "A" or "AA" (optional)
        page_url: URL of the page where the issue was found
        source: Finding source (axe-core, pa11y, manual)
        rule_id: Automated tool rule identifier
        description: Description of the accessibility issue
        severity: Severity level (critical, serious, moderate, minor, info)
        css_selector: CSS selector for the affected element
        html_snippet: HTML snippet of the affected element
        impact: Description of the accessibility impact
        remediation: Suggested fix for the issue
        status: Finding status (OPEN, CONFIRMED, DISMISSED, RESOLVED, WONT_FIX)
        reviewed_by: UUID of the reviewer (optional)
        reviewer_note: Note from the reviewer (optional)
        screenshot_key: MinIO storage key for finding screenshot
        screenshot_url: Presigned MinIO URL for screenshot (optional)
        created_at: When the finding was created
        updated_at: When the finding was last updated
        profile_relevant: Whether this finding is relevant for the active profile (optional)
        profile_priority: Priority level for the active profile (critical/high/medium/low/na) (optional)
        profile_severity: Boosted severity for the active profile (optional)
    """

    id: UUID
    evaluation_id: UUID
    page_id: UUID
    criterion_id: Optional[UUID] = None
    criterion_code: Optional[str] = None
    criterion_name: Optional[str] = None
    criterion_level: Optional[str] = None
    page_url: Optional[str] = None
    source: str
    rule_id: Optional[str] = None
    description: str
    severity: Optional[str] = None
    css_selector: Optional[str] = None
    html_snippet: Optional[str] = None
    impact: Optional[str] = None
    remediation: Optional[str] = None
    status: str = "OPEN"
    reviewed_by: Optional[UUID] = None
    reviewer_note: Optional[str] = None
    screenshot_key: Optional[str] = None
    screenshot_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Profile-specific fields (populated when ?profile= query param is used)
    profile_relevant: Optional[bool] = None
    profile_priority: Optional[str] = None  # critical/high/medium/low/na
    profile_severity: Optional[str] = None  # boosted severity for active profile

    model_config = ConfigDict(from_attributes=True)


class FindingCreate(BaseModel):
    """Schema for creating a new finding.

    Attributes:
        page_id: Page UUID where the issue was found
        criterion_id: WCAG criterion UUID
        description: Description of the accessibility issue
        severity: Severity level (critical, serious, moderate, minor, info)
        css_selector: CSS selector for the affected element (optional)
        html_snippet: HTML snippet of the affected element (optional)
    """

    page_id: UUID
    criterion_id: UUID
    description: str
    severity: str
    css_selector: Optional[str] = None
    html_snippet: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid_severities = ("critical", "serious", "moderate", "minor", "info")
        if v.lower() not in valid_severities:
            raise ValueError(f"Severity must be one of: {', '.join(valid_severities)}")
        return v.lower()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Validate that description is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty")
        return v

    model_config = ConfigDict(from_attributes=True)


class FindingUpdate(BaseModel):
    """Schema for updating a finding.

    All fields are optional - only provided fields will be updated.

    Attributes:
        status: Finding status (OPEN, CONFIRMED, DISMISSED, RESOLVED, WONT_FIX)
        reviewer_note: Note from the reviewer
        remediation: Suggested fix for the issue
    """

    status: Optional[str] = None
    reviewer_note: Optional[str] = None
    remediation: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate finding status if provided."""
        if v is None:
            return None
        valid_statuses = ("OPEN", "CONFIRMED", "DISMISSED", "RESOLVED", "WONT_FIX")
        if v.upper() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.upper()

    model_config = ConfigDict(from_attributes=True)


class FindingSummary(BaseModel):
    """Summary statistics for findings.

    Used to display finding counts by severity.

    Attributes:
        critical: Count of critical severity findings
        serious: Count of serious severity findings
        moderate: Count of moderate severity findings
        minor: Count of minor severity findings
        info: Count of info severity findings
        total: Total count of all findings
    """

    critical: int = 0
    serious: int = 0
    moderate: int = 0
    minor: int = 0
    info: int = 0
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class FindingListItem(BaseModel):
    """Lightweight finding representation for list views.

    Attributes:
        id: Finding UUID
        page_id: Page UUID
        page_url: URL of the page
        criterion_code: WCAG criterion code like "1.1.1"
        description: Description of the issue
        severity: Severity level
        status: Finding status
    """

    id: UUID
    page_id: UUID
    page_url: Optional[str] = None
    criterion_code: Optional[str] = None
    description: str
    severity: Optional[str] = None
    status: str = "OPEN"

    model_config = ConfigDict(from_attributes=True)


# Type alias for paginated finding response
FindingListResponse = PaginatedResponse[FindingResponse]


class ProfileSummaryInline(BaseModel):
    """
    Inline profile summary for findings response.

    Attributes:
        profile_id: Profile identifier
        profile_name: Human-readable profile name
        critical_for_profile: Count of findings with critical priority
        high_for_profile: Count of findings with high priority
        not_applicable: Count of findings marked N/A
        total_relevant: Count of relevant findings
        boosted_count: Count of findings with boosted severity
    """

    profile_id: str
    profile_name: str
    critical_for_profile: int = 0
    high_for_profile: int = 0
    not_applicable: int = 0
    total_relevant: int = 0
    boosted_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class FindingsWithProfileResponse(BaseModel):
    """
    Response for findings with profile summary.

    Includes the profile summary alongside the paginated findings list.

    Attributes:
        total: Total count of findings matching filters
        items: List of findings with profile fields
        profile_summary: Summary statistics for the active profile (optional)
    """

    total: int
    items: list[FindingResponse]
    profile_summary: Optional[ProfileSummaryInline] = None

    model_config = ConfigDict(from_attributes=True)
