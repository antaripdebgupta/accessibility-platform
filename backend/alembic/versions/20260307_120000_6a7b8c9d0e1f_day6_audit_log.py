"""day6_audit_log

Revision ID: 6a7b8c9d0e1f
Revises: 5c8b518a69b2
Create Date: 2026-03-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6a7b8c9d0e1f'
down_revision: Union[str, None] = '5c8b518a69b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True, comment='User who performed the action (null for system actions)'),
        sa.Column('organisation_id', sa.UUID(), nullable=True, comment='Organisation context for the action'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='Action identifier e.g. finding.confirmed, evaluation.created'),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='Entity type: finding, evaluation, page, report, scan, crawl'),
        sa.Column('entity_id', sa.UUID(), nullable=True, comment='ID of the entity that was affected'),
        sa.Column('before_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='State of the entity before the action (relevant fields only)'),
        sa.Column('after_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='State of the entity after the action (relevant fields only)'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP address of the client (IPv4 or IPv6)'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_org_created', 'audit_logs', ['organisation_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index('ix_audit_logs_org_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_table('audit_logs')
