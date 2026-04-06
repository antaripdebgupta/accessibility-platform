"""
User model.

Represents an authenticated user linked to Firebase Auth via firebase_uid.
Users can belong to multiple organisations with different roles.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.user_org_role import UserOrganisationRole
    from models.evaluation import EvaluationProject
    from models.finding import Finding
    from models.report import Report
    from models.invitation import Invitation


class User(Base):
    """User entity - represents an authenticated platform user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships
    organisation_roles: Mapped[List["UserOrganisationRole"]] = relationship(
        "UserOrganisationRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    created_evaluations: Mapped[List["EvaluationProject"]] = relationship(
        "EvaluationProject",
        back_populates="created_by_user",
        foreign_keys="EvaluationProject.created_by",
    )

    reviewed_findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="reviewer",
        foreign_keys="Finding.reviewed_by",
    )

    generated_reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="generated_by_user",
        foreign_keys="Report.generated_by",
    )

    sent_invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="inviter",
        foreign_keys="Invitation.invited_by",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', firebase_uid='{self.firebase_uid}')>"
