"""longitudinal_tables

Revision ID: 8c9d0e1f2a3b
Revises: 7b8c9d0e1f2a
Create Date: 2026-04-11 10:00:00.000000

Creates tables for longitudinal evaluation tracking:
- evaluation_series: Groups evaluations by target URL within an organisation
- series_snapshots: Point-in-time metrics for each evaluation in a series
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8c9d0e1f2a3b'
down_revision: Union[str, None] = '7b8c9d0e1f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create evaluation_series and series_snapshots tables."""

    # Create evaluation_series table
    op.create_table(
        'evaluation_series',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'organisation_id',
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            'target_url',
            sa.String(length=500),
            nullable=False,
            comment='Normalised target URL for the evaluation series',
        ),
        sa.Column(
            'display_name',
            sa.String(length=200),
            nullable=False,
            comment="Human-readable label for the series (e.g., 'ACME Homepage')",
        ),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['organisation_id'],
            ['organisations.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'organisation_id',
            'target_url',
            name='uq_evaluation_series_org_url',
        ),
    )

    # Create indexes for evaluation_series
    op.create_index(
        'ix_evaluation_series_organisation_id',
        'evaluation_series',
        ['organisation_id'],
        unique=False,
    )
    op.create_index(
        'ix_evaluation_series_org_url',
        'evaluation_series',
        ['organisation_id', 'target_url'],
        unique=False,
    )

    # Create series_snapshots table
    op.create_table(
        'series_snapshots',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'series_id',
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            'evaluation_id',
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            'snapshot_date',
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            comment='Date of the evaluation (taken from evaluation created_at)',
        ),
        sa.Column(
            'total_findings',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Total findings for this evaluation',
        ),
        sa.Column(
            'confirmed_findings',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Count of confirmed findings',
        ),
        sa.Column(
            'dismissed_findings',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Count of dismissed findings',
        ),
        sa.Column(
            'open_findings',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Count of open findings',
        ),
        sa.Column(
            'criteria_failed',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Count of distinct criteria with confirmed findings',
        ),
        sa.Column(
            'criteria_passed',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Count of criteria that passed (no confirmed findings)',
        ),
        sa.Column(
            'conformance_verdict',
            sa.String(length=30),
            nullable=True,
            comment='Verdict: CONFORMS, DOES_NOT_CONFORM, CANNOT_DETERMINE',
        ),
        sa.Column(
            'findings_by_severity',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Confirmed findings by severity: {"critical": N, "serious": N, ...}',
        ),
        sa.Column(
            'findings_by_criterion',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Confirmed findings by criterion ID: {"1.1.1": N, "1.4.3": N, ...}',
        ),
        sa.Column(
            'created_at',
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['series_id'],
            ['evaluation_series.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['evaluation_id'],
            ['evaluation_projects.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for series_snapshots
    op.create_index(
        'ix_series_snapshots_series_id',
        'series_snapshots',
        ['series_id'],
        unique=False,
    )
    op.create_index(
        'ix_series_snapshots_evaluation_id',
        'series_snapshots',
        ['evaluation_id'],
        unique=True,  # One snapshot per evaluation
    )
    op.create_index(
        'ix_series_snapshots_series_date',
        'series_snapshots',
        ['series_id', 'snapshot_date'],
        unique=False,
    )


def downgrade() -> None:
    """Drop series_snapshots and evaluation_series tables."""

    # Drop indexes for series_snapshots
    op.drop_index('ix_series_snapshots_series_date', table_name='series_snapshots')
    op.drop_index('ix_series_snapshots_evaluation_id', table_name='series_snapshots')
    op.drop_index('ix_series_snapshots_series_id', table_name='series_snapshots')

    # Drop series_snapshots table
    op.drop_table('series_snapshots')

    # Drop indexes for evaluation_series
    op.drop_index('ix_evaluation_series_org_url', table_name='evaluation_series')
    op.drop_index('ix_evaluation_series_organisation_id', table_name='evaluation_series')

    # Drop evaluation_series table
    op.drop_table('evaluation_series')
