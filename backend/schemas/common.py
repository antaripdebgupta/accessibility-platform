"""
Common Pydantic schemas used across the application.

Provides generic response models for pagination and async task status.
"""

from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Attributes:
        total: Total number of items matching the query
        items: List of items for the current page
    """

    total: int
    items: List[T]

    model_config = ConfigDict(from_attributes=True)


class TaskStatusResponse(BaseModel):
    """Response schema for async task status.

    Attributes:
        task_id: Celery task ID
        status: Current task status (PENDING, STARTED, SUCCESS, FAILURE, etc.)
    """

    task_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)
