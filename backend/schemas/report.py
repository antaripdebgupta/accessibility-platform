"""
Report-related Pydantic schemas.

Schemas for accessibility conformance reports including:
- Report creation requests
- Report responses with download URLs
- Verdict calculations
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FailedCriterionDetail(BaseModel):
    """Detail about a failed WCAG criterion."""

    criterion_code: str
    criterion_name: str
    finding_count: int

    model_config = ConfigDict(from_attributes=True)


class VerdictResult(BaseModel):
    """Result of conformance verdict calculation.

    Attributes:
        verdict: Overall conformance verdict
        criteria_passed: Number of criteria that passed
        criteria_failed: Number of criteria that failed
        failed_criteria: List of failed criteria with details
        total_findings: Total number of confirmed findings
    """

    verdict: str = Field(
        ...,
        description="CONFORMS, DOES_NOT_CONFORM, or CANNOT_DETERMINE",
    )
    criteria_passed: int = 0
    criteria_failed: int = 0
    failed_criteria: list[FailedCriterionDetail] = []
    total_findings: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    """Schema for requesting report generation.

    Attributes:
        report_types: List of report types to generate
        include_dismissed: Whether to include dismissed findings in the report
    """

    report_types: list[str] = Field(
        default=["full"],
        description="Report types to generate: executive, full, earl, csv",
    )
    include_dismissed: bool = Field(
        default=False,
        description="Whether to include dismissed findings in the report",
    )

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    """Schema for report response.

    Attributes:
        id: Report UUID
        evaluation_id: Parent evaluation UUID
        report_type: Type of report (executive, full, earl, csv)
        conformance_verdict: Overall conformance verdict
        criteria_passed: Number of passed criteria
        criteria_failed: Number of failed criteria
        criteria_na: Number of not applicable criteria
        total_findings: Total number of findings in report
        storage_key: MinIO storage key for the report file
        download_url: Presigned URL for downloading the report
        generated_at: When the report was generated
        generated_by: UUID of user who generated the report
    """

    id: UUID
    evaluation_id: UUID
    report_type: str
    conformance_verdict: Optional[str] = None
    criteria_passed: Optional[int] = None
    criteria_failed: Optional[int] = None
    criteria_na: Optional[int] = None
    total_findings: Optional[int] = None
    storage_key: Optional[str] = None
    download_url: Optional[str] = None
    generated_at: datetime
    generated_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Response schema for list of reports."""

    items: list[ReportResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class ReportGenerateResponse(BaseModel):
    """Response schema for report generation request."""

    task_id: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)
