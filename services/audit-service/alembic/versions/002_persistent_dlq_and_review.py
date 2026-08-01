"""
Migration: 002_persistent_dlq_and_review
Creates the failure_queue (dead-letter queue) table and review_tasks table
for durable state storage of failed workflows and clinician review items.
"""

from alembic import op
import sqlalchemy as sa

revision = "002_persistent_dlq_and_review"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "failure_queue",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(128), nullable=False, unique=True),
        sa.Column("service_name", sa.String(64), nullable=False),
        sa.Column("error_type", sa.String(128), nullable=False),
        sa.Column("error_message", sa.Text, nullable=False),
        sa.Column("retry_count", sa.Integer, nullable=False, default=0),
        sa.Column("max_retries", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, default="queued"),
        sa.Column("enqueued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redriven_by", sa.String(128), nullable=True),
        sa.Column("redriven_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_failure_queue_status", "failure_queue", ["status"])

    op.create_table(
        "review_tasks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(128), nullable=False),
        sa.Column("assigned_clinician_sub", sa.String(128), nullable=True),
        sa.Column("review_state", sa.String(32), nullable=False, default="pending"),
        sa.Column("decision_package_hash", sa.String(80), nullable=False),
        sa.Column("step_up_nonce", sa.String(256), nullable=True),
        sa.Column("signed_attestation_jti", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_tasks_state", "review_tasks", ["review_state"])
    op.create_index("ix_review_tasks_document", "review_tasks", ["document_id"])


def downgrade() -> None:
    op.drop_table("review_tasks")
    op.drop_table("failure_queue")
