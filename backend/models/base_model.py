"""
Shared base mixin for all SQLAlchemy models.

Provides common columns:
- id: UUID primary key with gen_random_uuid() default
- created_at: Timestamp with timezone, defaults to NOW()
- updated_at: Timestamp with timezone, auto-updates on change
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

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


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID primary key with gen_random_uuid() default."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class BaseModelMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """Combined mixin with UUID PK, created_at, and updated_at."""

    pass
