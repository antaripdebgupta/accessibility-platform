"""
Organisation model.

Represents a tenant/organisation in the multi-tenant platform.
Users belong to organisations via UserOrganisationRole.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.user_org_role import UserOrganisationRole
    from models.evaluation import EvaluationProject
    from models.invitation import Invitation
    from models.evaluation_series import EvaluationSeries


class Organisation(Base):
    """Organisation entity - represents a tenant in the platform."""

    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
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
    user_roles: Mapped[List["UserOrganisationRole"]] = relationship(
        "UserOrganisationRole",
        back_populates="organisation",
        cascade="all, delete-orphan",
    )

    evaluations: Mapped[List["EvaluationProject"]] = relationship(
        "EvaluationProject",
        back_populates="organisation",
        cascade="all, delete-orphan",
    )

    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="organisation",
        cascade="all, delete-orphan",
    )

    evaluation_series: Mapped[List["EvaluationSeries"]] = relationship(
        "EvaluationSeries",
        back_populates="organisation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organisation(id={self.id}, name='{self.name}', slug='{self.slug}')>"
