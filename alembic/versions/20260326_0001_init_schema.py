"""Create initial payments and outbox schema.

Revision ID: 20260326_0001
Revises:
Create Date: 2026-03-26 20:40:00
"""
from alembic import op

revision = "20260326_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("DO $$ BEGIN CREATE TYPE currency AS ENUM ('RUB', 'USD', 'EUR'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute(
        "DO $$ BEGIN CREATE TYPE payment_status AS ENUM ('pending', 'succeeded', 'failed'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id VARCHAR PRIMARY KEY,
            amount NUMERIC(18, 2) NOT NULL,
            currency currency NOT NULL,
            description VARCHAR,
            meta JSON,
            status payment_status NOT NULL DEFAULT 'pending',
            idempotency_key VARCHAR UNIQUE NOT NULL,
            webhook_url VARCHAR,
            created_at TIMESTAMPTZ DEFAULT now(),
            processed_at TIMESTAMPTZ
        );
        """
    )
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
    op.drop_table("outbox")
    op.drop_table("payments")
    op.execute("DROP TYPE IF EXISTS payment_status;")
    op.execute("DROP TYPE IF EXISTS currency;")
