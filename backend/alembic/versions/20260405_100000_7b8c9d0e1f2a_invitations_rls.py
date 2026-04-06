"""add_invitations_and_rls_policies

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-04-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7b8c9d0e1f2a'
down_revision: Union[str, None] = '6a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add invitations table and enable Row-Level Security on data tables."""
    op.create_table(
        'invitations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organisation_id', sa.UUID(), nullable=False),
        sa.Column('invited_by', sa.UUID(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('token', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('accepted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'expired', 'revoked')",
            name='ck_invitation_status_valid'
        ),
        sa.CheckConstraint(
            "role IN ('auditor', 'reviewer', 'viewer')",
            name='ck_invitation_role_valid'
        ),
    )

    # Indexes for invitations
    op.create_index('ix_invitations_token', 'invitations', ['token'], unique=True)
    op.create_index('ix_invitations_org_status', 'invitations', ['organisation_id', 'status'], unique=False)
    op.create_index('ix_invitations_email', 'invitations', ['email'], unique=False)

    # Enable Row-Level Security on data tables

    # Enable RLS on evaluation_projects
    op.execute("ALTER TABLE evaluation_projects ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY eval_isolation ON evaluation_projects
        USING (organisation_id::text = current_setting('app.current_org_id', true))
    """)
    op.execute("ALTER TABLE evaluation_projects FORCE ROW LEVEL SECURITY")

    # Enable RLS on pages (via evaluation)
    op.execute("ALTER TABLE pages ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY page_isolation ON pages
        USING (
            evaluation_id IN (
                SELECT id FROM evaluation_projects
                WHERE organisation_id::text = current_setting('app.current_org_id', true)
            )
        )
    """)
    op.execute("ALTER TABLE pages FORCE ROW LEVEL SECURITY")

    # Enable RLS on findings (via evaluation)
    op.execute("ALTER TABLE findings ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY finding_isolation ON findings
        USING (
            evaluation_id IN (
                SELECT id FROM evaluation_projects
                WHERE organisation_id::text = current_setting('app.current_org_id', true)
            )
        )
    """)
    op.execute("ALTER TABLE findings FORCE ROW LEVEL SECURITY")

    # Enable RLS on reports (via evaluation)
    op.execute("ALTER TABLE reports ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY report_isolation ON reports
        USING (
            evaluation_id IN (
                SELECT id FROM evaluation_projects
                WHERE organisation_id::text = current_setting('app.current_org_id', true)
            )
        )
    """)
    op.execute("ALTER TABLE reports FORCE ROW LEVEL SECURITY")

    # Grant BYPASSRLS to celery_worker role if it exists
    # allows background tasks to access all data without RLS filtering
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'celery_worker') THEN
                ALTER ROLE celery_worker BYPASSRLS;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove RLS policies and invitations table."""

    # Revoke BYPASSRLS from celery_worker if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'celery_worker') THEN
                ALTER ROLE celery_worker NOBYPASSRLS;
            END IF;
        END $$;
    """)

    # Disable RLS and drop policies on reports
    op.execute("DROP POLICY IF EXISTS report_isolation ON reports")
    op.execute("ALTER TABLE reports DISABLE ROW LEVEL SECURITY")

    # Disable RLS and drop policies on findings
    op.execute("DROP POLICY IF EXISTS finding_isolation ON findings")
    op.execute("ALTER TABLE findings DISABLE ROW LEVEL SECURITY")

    # Disable RLS and drop policies on pages
    op.execute("DROP POLICY IF EXISTS page_isolation ON pages")
    op.execute("ALTER TABLE pages DISABLE ROW LEVEL SECURITY")

    # Disable RLS and drop policies on evaluation_projects
    op.execute("DROP POLICY IF EXISTS eval_isolation ON evaluation_projects")
    op.execute("ALTER TABLE evaluation_projects DISABLE ROW LEVEL SECURITY")

    # Drop invitations table
    op.drop_index('ix_invitations_email', table_name='invitations')
    op.drop_index('ix_invitations_org_status', table_name='invitations')
    op.drop_index('ix_invitations_token', table_name='invitations')
    op.drop_table('invitations')
