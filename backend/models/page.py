"""
Page model.

Represents a discovered page within an evaluation project.
Pages are found via crawling and can be selected for sampling and scanning.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Boolean, SmallInteger, Text, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.evaluation import EvaluationProject
    from models.finding import Finding


# Valid crawl/scan statuses
VALID_CRAWL_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETE", "FAILED")
VALID_SCAN_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETE", "FAILED")


class Page(Base):
    """Page entity - represents a discovered page within an evaluation."""

    __tablename__ = "pages"

    __table_args__ = (
        UniqueConstraint("evaluation_id", "url", name="uq_evaluation_page_url"),
        Index("ix_pages_evaluation_id", "evaluation_id"),
        Index("ix_pages_evaluation_in_sample", "evaluation_id", "in_sample"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    page_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Page type classification: homepage, contact, product, etc.",
    )

    title: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    in_sample: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    sample_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reason for including in sample: homepage, process-start, common-type, etc.",
    )

    crawl_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    scan_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    discovered_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    scanned_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    http_status: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    screenshot_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO storage key for page screenshot",
    )

    # Relationships
    evaluation: Mapped["EvaluationProject"] = relationship(
        "EvaluationProject",
        back_populates="pages",
    )

    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="page",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Page(id={self.id}, url='{self.url[:50]}...', in_sample={self.in_sample})>"
