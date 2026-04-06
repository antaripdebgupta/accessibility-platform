"""
Invitation model.

Represents an invitation to join an organisation.
Invitations have a unique token for secure access, expiration, and status tracking.
"""

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.organisation import Organisation
    from models.user import User


# Valid invitation statuses
VALID_STATUSES = ("pending", "accepted", "expired", "revoked")

# Valid roles that can be assigned via invitation (owner excluded - only for org creators)
VALID_INVITATION_ROLES = ("auditor", "reviewer", "viewer")


def get_default_expiry() -> datetime:
    """Return datetime 7 days from now for invitation expiry."""
    return datetime.utcnow() + timedelta(days=7)


class Invitation(Base):
    """Invitation entity - represents an invitation to join an organisation."""

    __tablename__ = "invitations"

    __table_args__ = (
        Index("ix_invitations_token", "token", unique=True),
        Index("ix_invitations_org_status", "organisation_id", "status"),
        Index("ix_invitations_email", "email"),
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

    invited_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Role to assign: auditor, reviewer, or viewer",
    )

    token: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Status: pending, accepted, expired, or revoked",
    )

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=get_default_expiry,
    )

    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # Relationships
    organisation: Mapped["Organisation"] = relationship(
        "Organisation",
        back_populates="invitations",
    )

    inviter: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="sent_invitations",
        foreign_keys=[invited_by],
    )

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email='{self.email}', status='{self.status}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None) if self.expires_at else True

    @property
    def is_valid(self) -> bool:
        """Check if the invitation is still valid (pending and not expired)."""
        return self.status == "pending" and not self.is_expired
