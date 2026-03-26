"""Ensure outbox table exists for outbox pattern.

Revision ID: 20260326_0002
Revises: 20260326_0001
Create Date: 2026-03-26 20:58:00
"""

from alembic import op

revision = "20260326_0002"
down_revision = "20260326_0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox (
            id VARCHAR PRIMARY KEY,
            aggregate_id VARCHAR NOT NULL,
            event_type VARCHAR NOT NULL,
            payload JSON NOT NULL,
            published BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ,
            published_at TIMESTAMP
        );
        """
    )

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS outbox;")
