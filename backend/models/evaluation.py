"""
EvaluationProject model.

Represents a WCAG accessibility evaluation project following WCAG-EM methodology.
Tracks the lifecycle from DRAFT through COMPLETE with scope, pages, findings, and reports.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.organisation import Organisation
    from models.user import User
    from models.page import Page
    from models.finding import Finding
    from models.report import Report


# Valid evaluation statuses following WCAG-EM workflow
VALID_STATUSES = (
    "DRAFT",
    "SCOPING",
    "EXPLORING",
    "SAMPLING",
    "AUDITING",
    "REPORTING",
    "COMPLETE",
    "DELETED",
)

# Valid audit types
VALID_AUDIT_TYPES = ("in-depth", "quick-scan", "sample-based")


class EvaluationProject(Base):
    """WCAG accessibility evaluation project entity."""

    __tablename__ = "evaluation_projects"

    __table_args__ = (
        Index("ix_evaluation_projects_organisation_id", "organisation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    target_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    wcag_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="2.1",
    )

    conformance_level: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="AA",
    )

    audit_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in-depth",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
    )

    scope_config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Configuration for crawl scope: include/exclude patterns, max pages, etc.",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    # Relationships
    organisation: Mapped["Organisation"] = relationship(
        "Organisation",
        back_populates="evaluations",
    )

    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_evaluations",
        foreign_keys=[created_by],
    )

    pages: Mapped[List["Page"]] = relationship(
        "Page",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )

    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )

    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<EvaluationProject(id={self.id}, title='{self.title}', status='{self.status}')>"
