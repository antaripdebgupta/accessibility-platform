"""
EvaluationSeries model.

Represents a series of evaluations for the same website within an organisation.
Used for longitudinal tracking to compare accessibility over time.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.organisation import Organisation
    from models.series_snapshot import SeriesSnapshot


class EvaluationSeries(Base):
    """
    Evaluation series entity.

    Groups multiple evaluations of the same website for longitudinal analysis.
    Each unique (organisation_id, target_url) pair maps to one series.
    """

    __tablename__ = "evaluation_series"

    __table_args__ = (
        UniqueConstraint(
            "organisation_id",
            "target_url",
            name="uq_evaluation_series_org_url",
        ),
        Index(
            "ix_evaluation_series_org_url",
            "organisation_id",
            "target_url",
        ),
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
        index=True,
    )

    target_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Normalised target URL for the evaluation series",
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable label for the series (e.g., 'ACME Homepage')",
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
        back_populates="evaluation_series",
    )

    snapshots: Mapped[List["SeriesSnapshot"]] = relationship(
        "SeriesSnapshot",
        back_populates="series",
        cascade="all, delete-orphan",
        order_by="SeriesSnapshot.snapshot_date.asc()",
    )

    def __repr__(self) -> str:
        return f"<EvaluationSeries(id={self.id}, display_name='{self.display_name}', target_url='{self.target_url}')>"
