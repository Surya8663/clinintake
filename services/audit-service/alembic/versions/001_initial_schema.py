"""
Migration: 001_initial_schema
Creates the audit_vault table with HMAC-signed append-only event records
and the document_workflow table for persistent workflow state.
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_vault",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(128), nullable=False, unique=True),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_name", sa.String(64), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("document_id", sa.String(128), nullable=True),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("lyzr_execution_id", sa.String(128), nullable=True),
        sa.Column("prev_hash", sa.String(80), nullable=False),
        sa.Column("entry_hash", sa.String(80), nullable=False),
        sa.Column("hmac_signature", sa.Text, nullable=False),
    )
    op.create_index("ix_audit_vault_document_id", "audit_vault", ["document_id"])
    op.create_index("ix_audit_vault_trace_id", "audit_vault", ["trace_id"])
    op.create_index("ix_audit_vault_sequence", "audit_vault", ["sequence"])

    op.create_table(
        "document_workflow",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(128), nullable=False, unique=True),
        sa.Column("workflow_state", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, default=1),
        sa.Column("idempotency_key", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_workflow_state", "document_workflow", ["workflow_state"])


def downgrade() -> None:
    op.drop_table("document_workflow")
    op.drop_table("audit_vault")
