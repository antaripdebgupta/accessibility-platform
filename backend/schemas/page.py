"""
Page-related Pydantic schemas.

Schemas for page entities within an evaluation project.
Pages are discovered via crawling and can be selected for sampling and scanning.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.common import PaginatedResponse


class PageResponse(BaseModel):
    """Schema for page response.

    Represents a discovered page within an evaluation project.

    Attributes:
        id: Page UUID
        evaluation_id: Parent evaluation UUID
        url: Full URL of the page
        title: Page title (from <title> tag)
        page_type: Classification (homepage, contact, product, etc.)
        in_sample: Whether this page is included in the audit sample
        crawl_status: Status of crawling (PENDING, IN_PROGRESS, COMPLETE, FAILED)
        scan_status: Status of scanning (PENDING, IN_PROGRESS, COMPLETE, FAILED)
        http_status: HTTP response status code
        screenshot_key: MinIO storage key for page screenshot
        discovered_at: When the page was discovered during crawling
        scanned_at: When the page was scanned for accessibility issues
    """

    id: UUID
    evaluation_id: UUID
    url: str
    title: Optional[str] = None
    page_type: Optional[str] = None
    in_sample: bool = False
    crawl_status: str = "PENDING"
    scan_status: str = "PENDING"
    http_status: Optional[int] = None
    screenshot_key: Optional[str] = None
    discovered_at: Optional[datetime] = None
    scanned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PageCreate(BaseModel):
    """Schema for creating a new page.

    Attributes:
        evaluation_id: Parent evaluation UUID
        url: Full URL of the page
        title: Optional page title
        page_type: Optional classification
    """

    evaluation_id: UUID
    url: str
    title: Optional[str] = None
    page_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PageUpdate(BaseModel):
    """Schema for updating a page.

    All fields are optional - only provided fields will be updated.

    Attributes:
        title: Page title
        page_type: Page classification
        in_sample: Whether to include in audit sample
        sample_reason: Reason for including in sample
        crawl_status: Crawl status
        scan_status: Scan status
    """

    title: Optional[str] = None
    page_type: Optional[str] = None
    in_sample: Optional[bool] = None
    sample_reason: Optional[str] = None
    crawl_status: Optional[str] = None
    scan_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PageListItem(BaseModel):
    """Lightweight page representation for list views.

    Attributes:
        id: Page UUID
        url: Full URL of the page
        title: Page title
        page_type: Classification
        in_sample: Whether included in sample
        crawl_status: Crawl status
        scan_status: Scan status
    """

    id: UUID
    url: str
    title: Optional[str] = None
    page_type: Optional[str] = None
    in_sample: bool = False
    crawl_status: str = "PENDING"
    scan_status: str = "PENDING"

    model_config = ConfigDict(from_attributes=True)


# Type alias for paginated page response
PageListResponse = PaginatedResponse[PageResponse]
