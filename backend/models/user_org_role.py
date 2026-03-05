"""
UserOrganisationRole model.

Junction table that links users to organisations with a specific role.
Enforces that each user can have only one role per organisation.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.user import User
    from models.organisation import Organisation


# Valid roles for organisation membership
VALID_ROLES = ("owner", "auditor", "reviewer", "viewer")


class UserOrganisationRole(Base):
    """Junction table for user-organisation membership with roles."""

    __tablename__ = "user_organisation_roles"

    __table_args__ = (
        UniqueConstraint("user_id", "organisation_id", name="uq_user_organisation"),
        CheckConstraint(
            f"role IN {VALID_ROLES}",
            name="ck_user_org_role_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="organisation_roles",
    )

    organisation: Mapped["Organisation"] = relationship(
        "Organisation",
        back_populates="user_roles",
    )

    def __repr__(self) -> str:
        return f"<UserOrganisationRole(user_id={self.user_id}, organisation_id={self.organisation_id}, role='{self.role}')>"
