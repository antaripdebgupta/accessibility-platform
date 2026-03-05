"""
Report model.

Represents a generated report for an evaluation project.
Supports multiple formats: executive summary, full report, EARL, CSV.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.evaluation import EvaluationProject
    from models.user import User


# Valid report types
VALID_REPORT_TYPES = ("executive", "full", "earl", "csv")

# Valid conformance verdicts
VALID_VERDICTS = ("CONFORMS", "DOES_NOT_CONFORM", "CANNOT_DETERMINE")


class Report(Base):
    """Report entity - represents a generated accessibility report."""

    __tablename__ = "reports"

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
        index=True,
    )

    generated_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    report_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Report type: executive, full, earl, csv",
    )

    conformance_verdict: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Verdict: CONFORMS, DOES_NOT_CONFORM, CANNOT_DETERMINE",
    )

    criteria_passed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    criteria_failed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    criteria_na: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Criteria marked as not applicable",
    )

    total_findings: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    storage_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO storage key for the report file",
    )

    generated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # Relationships
    evaluation: Mapped["EvaluationProject"] = relationship(
        "EvaluationProject",
        back_populates="reports",
    )

    generated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="generated_reports",
        foreign_keys=[generated_by],
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type='{self.report_type}', verdict='{self.conformance_verdict}')>"
