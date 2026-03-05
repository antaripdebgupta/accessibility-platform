"""
WcagCriterion model.

Stores WCAG 2.1 and 2.2 success criteria for reference during audits.
Each criterion has an ID (e.g., "1.1.1"), name, level, and description.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.finding import Finding


# Valid WCAG conformance levels
VALID_LEVELS = ("A", "AA", "AAA")


class WcagCriterion(Base):
    """WCAG Success Criterion reference entity."""

    __tablename__ = "wcag_criteria"

    __table_args__ = (
        CheckConstraint(
            f"level IN {VALID_LEVELS}",
            name="ck_wcag_level_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    criterion_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="WCAG criterion identifier, e.g., '1.1.1'",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    level: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="Conformance level: A, AA, or AAA",
    )

    wcag_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="2.1",
        comment="WCAG version: 2.1 or 2.2",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    understanding_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Link to W3C Understanding document",
    )

    # Relationships
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="criterion",
    )

    def __repr__(self) -> str:
        return f"<WcagCriterion(criterion_id='{self.criterion_id}', name='{self.name}', level='{self.level}')>"
