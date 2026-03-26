"""Align payment_status enum values with spec.

Revision ID: 20260326_0003
Revises: 20260326_0002
Create Date: 2026-03-26 21:20:00
"""

from alembic import op

revision = "20260326_0003"
down_revision = "20260326_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # If old values exist, rename them to match spec.
    op.execute(
        "DO $$ BEGIN "
        "ALTER TYPE payment_status RENAME VALUE 'success' TO 'succeeded'; "
        "EXCEPTION WHEN undefined_object OR invalid_parameter_value THEN NULL; "
        "END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "ALTER TYPE payment_status RENAME VALUE 'failure' TO 'failed'; "
        "EXCEPTION WHEN undefined_object OR invalid_parameter_value THEN NULL; "
        "END $$;"
    )
    # Ensure new values exist (for DBs created directly with new type).
    op.execute(
        "DO $$ BEGIN "
        "ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'succeeded'; "
        "EXCEPTION WHEN undefined_object THEN NULL; "
        "END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'failed'; "
        "EXCEPTION WHEN undefined_object THEN NULL; "
        "END $$;"
    )

def downgrade() -> None:
    # Irreversible safely for enums; keep as no-op.
    pass

