"""
Finding model.

Represents an accessibility issue found during an evaluation.
Findings can come from automated tools (axe-core, pa11y) or manual review.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.evaluation import EvaluationProject
    from models.page import Page
    from models.wcag import WcagCriterion
    from models.user import User


# Valid finding sources
VALID_SOURCES = ("axe-core", "pa11y", "manual")

# Valid severity levels
VALID_SEVERITIES = ("critical", "serious", "moderate", "minor", "info")

# Valid finding statuses
VALID_STATUSES = ("OPEN", "CONFIRMED", "DISMISSED", "RESOLVED", "WONT_FIX")


class Finding(Base):
    """Accessibility finding entity - represents an issue found during evaluation."""

    __tablename__ = "findings"

    __table_args__ = (
        Index("ix_findings_evaluation_id", "evaluation_id"),
        Index("ix_findings_page_id", "page_id"),
        Index("ix_findings_criterion_id", "criterion_id"),
        Index("ix_findings_evaluation_status", "evaluation_id", "status"),
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

    page_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )

    criterion_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("wcag_criteria.id", ondelete="SET NULL"),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Finding source: axe-core, pa11y, or manual",
    )

    rule_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Automated tool rule identifier",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Severity: critical, serious, moderate, minor, info",
    )

    css_selector: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    html_snippet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    impact: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the accessibility impact",
    )

    remediation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Suggested fix for the issue",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )

    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewer_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    screenshot_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO storage key for finding screenshot",
    )

    raw_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Raw JSON result from automated tool",
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
    evaluation: Mapped["EvaluationProject"] = relationship(
        "EvaluationProject",
        back_populates="findings",
    )

    page: Mapped["Page"] = relationship(
        "Page",
        back_populates="findings",
    )

    criterion: Mapped[Optional["WcagCriterion"]] = relationship(
        "WcagCriterion",
        back_populates="findings",
    )

    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviewed_findings",
        foreign_keys=[reviewed_by],
    )

    def __repr__(self) -> str:
        return f"<Finding(id={self.id}, source='{self.source}', severity='{self.severity}', status='{self.status}')>"
