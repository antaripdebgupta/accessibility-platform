"""
Pydantic Schemas Package.

This module exports all schema classes for use in API routes.
"""

from schemas.common import PaginatedResponse, TaskStatusResponse
from schemas.auth import OrgMembership, UserResponse
from schemas.evaluation import (
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationResponse,
    EvaluationListItem,
)
from schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
    ReportGenerateResponse,
    VerdictResult,
    FailedCriterionDetail,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "TaskStatusResponse",
    # Auth
    "OrgMembership",
    "UserResponse",
    # Evaluation
    "EvaluationCreate",
    "EvaluationUpdate",
    "EvaluationResponse",
    "EvaluationListItem",
    # Report
    "ReportCreate",
    "ReportResponse",
    "ReportListResponse",
    "ReportGenerateResponse",
    "VerdictResult",
    "FailedCriterionDetail",
]
