#!/usr/bin/env python3
"""
Development seed script.

Creates test data for local development:
- 1 Organisation (Dev Org)
- 1 User (dev@example.com)
- 1 UserOrganisationRole (owner)

Uses upsert pattern - safe to run multiple times.

Usage:
    python -m scripts.seed_dev

Or run directly:
    python scripts/seed_dev.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings


async def seed_dev_data():
    """Insert development test data into the database."""
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        # Upsert Organisation
        org_sql = text("""
            INSERT INTO organisations (name, slug)
            VALUES (:name, :slug)
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = NOW()
            RETURNING id, (xmax = 0) AS inserted
        """)
        org_result = await conn.execute(
            org_sql,
            {"name": "Dev Org", "slug": "dev-org"},
        )
        org_row = org_result.fetchone()
        assert org_row is not None
        org_id = org_row[0]
        org_inserted = org_row[1]

        # Upsert User
        user_sql = text("""
            INSERT INTO users (firebase_uid, email, display_name)
            VALUES (:firebase_uid, :email, :display_name)
            ON CONFLICT (firebase_uid) DO UPDATE SET
                email = EXCLUDED.email,
                display_name = EXCLUDED.display_name
            RETURNING id, (xmax = 0) AS inserted
        """)
        user_result = await conn.execute(
            user_sql,
            {
                "firebase_uid": "dev-uid-000",
                "email": "dev@example.com",
                "display_name": "Dev User",
            },
        )
        user_row = user_result.fetchone()
        assert user_row is not None
        user_id = user_row[0]
        user_inserted = user_row[1]

        # Upsert UserOrganisationRole
        role_sql = text("""
            INSERT INTO user_organisation_roles (user_id, organisation_id, role)
            VALUES (:user_id, :organisation_id, :role)
            ON CONFLICT ON CONSTRAINT uq_user_organisation DO UPDATE SET
                role = EXCLUDED.role
            RETURNING id, (xmax = 0) AS inserted
        """)
        role_result = await conn.execute(
            role_sql,
            {
                "user_id": user_id,
                "organisation_id": org_id,
                "role": "owner",
            },
        )
        role_row = role_result.fetchone()
        assert role_row is not None
        role_inserted = role_row[1]

        print(f"\n{'=' * 60}")
        print("Development Seed Complete")
        print(f"{'=' * 60}")
        print(f"\nOrganisation:")
        print(f"  ID:      {org_id}")
        print(f"  Name:    Dev Org")
        print(f"  Slug:    dev-org")
        print(f"  Status:  {'Created' if org_inserted else 'Updated'}")
        print(f"\nUser:")
        print(f"  ID:           {user_id}")
        print(f"  Firebase UID: dev-uid-000")
        print(f"  Email:        dev@example.com")
        print(f"  Display Name: Dev User")
        print(f"  Status:       {'Created' if user_inserted else 'Updated'}")
        print(f"\nOrganisation Role:")
        print(f"  Role:   owner")
        print(f"  Status: {'Created' if role_inserted else 'Updated'}")
        print(f"\n{'=' * 60}")
        print("\nDev bypass token for local testing:")
        print("  Authorization: Bearer dev-bypass-token-local-only")
        print(f"{'=' * 60}\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_dev_data())
