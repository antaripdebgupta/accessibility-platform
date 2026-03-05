"""
Evaluation-related Pydantic schemas.

Schemas for creating, updating, and responding with evaluation projects.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class EvaluationCreate(BaseModel):
    """Schema for creating a new evaluation project.

    Attributes:
        title: Project title
        target_url: Website URL to evaluate (must be http/https)
        wcag_version: WCAG version to evaluate against (default: 2.1)
        conformance_level: Target conformance level (default: AA)
        audit_type: Type of audit (default: in-depth)
    """

    title: str
    target_url: str
    wcag_version: str = "2.1"
    conformance_level: str = "AA"
    audit_type: str = "in-depth"

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL starts with http:// or https://."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or less")
        return v

    @field_validator("wcag_version")
    @classmethod
    def validate_wcag_version(cls, v: str) -> str:
        """Validate WCAG version."""
        valid_versions = ("2.0", "2.1", "2.2")
        if v not in valid_versions:
            raise ValueError(f"WCAG version must be one of: {', '.join(valid_versions)}")
        return v

    @field_validator("conformance_level")
    @classmethod
    def validate_conformance_level(cls, v: str) -> str:
        """Validate conformance level."""
        valid_levels = ("A", "AA", "AAA")
        if v not in valid_levels:
            raise ValueError(f"Conformance level must be one of: {', '.join(valid_levels)}")
        return v

    @field_validator("audit_type")
    @classmethod
    def validate_audit_type(cls, v: str) -> str:
        """Validate audit type."""
        valid_types = ("in-depth", "quick-scan", "sample-based")
        if v not in valid_types:
            raise ValueError(f"Audit type must be one of: {', '.join(valid_types)}")
        return v

    model_config = ConfigDict(from_attributes=True)


class EvaluationUpdate(BaseModel):
    """Schema for updating an evaluation project.

    All fields are optional - only provided fields will be updated.
    Note: status cannot be changed via this endpoint.
    """

    title: Optional[str] = None
    target_url: Optional[str] = None
    wcag_version: Optional[str] = None
    conformance_level: Optional[str] = None
    audit_type: Optional[str] = None
    scope_config: Optional[dict[str, Any]] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title is not empty if provided."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL if provided."""
        if v is None:
            return v
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or less")
        return v

    @field_validator("wcag_version")
    @classmethod
    def validate_wcag_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate WCAG version if provided."""
        if v is None:
            return v
        valid_versions = ("2.0", "2.1", "2.2")
        if v not in valid_versions:
            raise ValueError(f"WCAG version must be one of: {', '.join(valid_versions)}")
        return v

    @field_validator("conformance_level")
    @classmethod
    def validate_conformance_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate conformance level if provided."""
        if v is None:
            return v
        valid_levels = ("A", "AA", "AAA")
        if v not in valid_levels:
            raise ValueError(f"Conformance level must be one of: {', '.join(valid_levels)}")
        return v

    @field_validator("audit_type")
    @classmethod
    def validate_audit_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate audit type if provided."""
        if v is None:
            return v
        valid_types = ("in-depth", "quick-scan", "sample-based")
        if v not in valid_types:
            raise ValueError(f"Audit type must be one of: {', '.join(valid_types)}")
        return v

    model_config = ConfigDict(from_attributes=True)


class EvaluationResponse(BaseModel):
    """Full evaluation project response.

    Includes all fields for detailed view.
    """

    id: UUID
    organisation_id: UUID
    created_by: Optional[UUID] = None
    title: str
    target_url: str
    wcag_version: str
    conformance_level: str
    audit_type: str
    status: str
    scope_config: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationListItem(BaseModel):
    """Evaluation project summary for list views.

    Includes only essential fields for display in lists.
    """

    id: UUID
    title: str
    target_url: str
    status: str
    wcag_version: str
    conformance_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
