"""
SeriesSnapshot model.

Represents a point-in-time snapshot of an evaluation within a series.
Captures aggregate metrics for longitudinal trend analysis.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.evaluation_series import EvaluationSeries
    from models.evaluation import EvaluationProject


class SeriesSnapshot(Base):
    """
    Series snapshot entity.

    Captures a point-in-time view of an evaluation's accessibility metrics
    for use in longitudinal trend analysis. Each evaluation can have at most
    one snapshot in a series.
    """

    __tablename__ = "series_snapshots"

    __table_args__ = (
        Index(
            "ix_series_snapshots_series_date",
            "series_id",
            "snapshot_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    series_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_series.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluation_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One snapshot per evaluation
        index=True,
    )

    snapshot_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Date of the evaluation (taken from evaluation created_at)",
    )

    # Aggregate finding counts
    total_findings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total findings for this evaluation",
    )

    confirmed_findings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of confirmed findings",
    )

    dismissed_findings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of dismissed findings",
    )

    open_findings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of open findings",
    )

    criteria_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of distinct criteria with confirmed findings",
    )

    criteria_passed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of criteria that passed (no confirmed findings)",
    )

    conformance_verdict: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Verdict: CONFORMS, DOES_NOT_CONFORM, CANNOT_DETERMINE",
    )

    # JSONB aggregates for detailed analysis
    findings_by_severity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Confirmed findings by severity: {"critical": N, "serious": N, ...}',
    )

    findings_by_criterion: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Confirmed findings by criterion ID: {"1.1.1": N, "1.4.3": N, ...}',
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # Relationships
    series: Mapped["EvaluationSeries"] = relationship(
        "EvaluationSeries",
        back_populates="snapshots",
    )

    evaluation: Mapped["EvaluationProject"] = relationship(
        "EvaluationProject",
        backref="series_snapshot",
    )

    def __repr__(self) -> str:
        return (
            f"<SeriesSnapshot(id={self.id}, series_id={self.series_id}, "
            f"snapshot_date='{self.snapshot_date}', confirmed_findings={self.confirmed_findings})>"
        )
