"""initial schema with RLS

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clerk_user_id", sa.String(), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("preferred_source_lang", sa.String(8), nullable=False, server_default="ja"),
        sa.Column("preferred_target_lang", sa.String(8), nullable=False, server_default="en"),
        sa.Column("plan", sa.String(), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("pinned_vocabulary", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("consent_recording_ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_s", sa.Integer(), server_default="0"),
        sa.Column("source_language", sa.String(8), server_default="ja"),
        sa.Column("target_language", sa.String(8), server_default="en"),
        sa.Column("status", sa.String(), server_default="recording"),
        sa.Column("template", sa.String(), server_default="default"),
        sa.Column("google_meet_code", sa.String(), nullable=True),
        sa.Column(
            "participant_names",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("decisions", postgresql.JSONB(), server_default="[]"),
        sa.Column("action_items", postgresql.JSONB(), server_default="[]"),
        sa.Column("open_questions", postgresql.JSONB(), server_default="[]"),
        sa.Column("glossary", postgresql.JSONB(), server_default="[]"),
        sa.Column("stt_cost_cents", sa.Integer(), server_default="0"),
        sa.Column("llm_cost_cents", sa.Integer(), server_default="0"),
        sa.Column("is_saved", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("transcript_s3_key", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_meetings_user_id", "meetings", ["user_id"])

    op.create_table(
        "utterances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("speaker_id", sa.String(), server_default="0"),
        sa.Column("speaker_name", sa.String(), nullable=True),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("original_text_tsv", postgresql.TSVECTOR(), nullable=True),
        sa.Column("translated_text", sa.Text(), nullable=True),
        sa.Column("translated_text_tsv", postgresql.TSVECTOR(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("qdrant_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_important", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("utterances_meeting_idx", "utterances", ["meeting_id", "start_ms"])
    op.create_index(
        "utterances_orig_tsv",
        "utterances",
        ["original_text_tsv"],
        postgresql_using="gin",
    )
    op.create_index(
        "utterances_trans_tsv",
        "utterances",
        ["translated_text_tsv"],
        postgresql_using="gin",
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION utterance_tsv_update() RETURNS trigger AS $$
        BEGIN
          NEW.original_text_tsv := to_tsvector('simple', coalesce(NEW.original_text, ''));
          NEW.translated_text_tsv := to_tsvector('simple', coalesce(NEW.translated_text, ''));
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER utterance_tsv_trigger
          BEFORE INSERT OR UPDATE OF original_text, translated_text ON utterances
          FOR EACH ROW EXECUTE FUNCTION utterance_tsv_update();
        """
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_meeting_id", "chat_messages", ["meeting_id"])

    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("minutes_transcribed", sa.Integer(), server_default="0"),
        sa.Column("llm_tokens_in", sa.Integer(), server_default="0"),
        sa.Column("llm_tokens_out", sa.Integer(), server_default="0"),
        sa.Column("stt_cost_cents", sa.Integer(), server_default="0"),
        sa.Column("llm_cost_cents", sa.Integer(), server_default="0"),
        sa.UniqueConstraint("user_id", "date", name="uq_usage_user_date"),
    )

    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default="{}"),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_integrations_user_id", "integrations", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # RLS: enforce per-user isolation. Policies read user_id from the
    # `app.user_id` GUC which API sets via `SELECT set_config('app.user_id', :uid, true)`
    # at the start of every request-scoped session.
    for table in ("meetings", "chat_messages", "integrations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_user_isolation ON {table}
            USING (user_id::text = current_setting('app.user_id', true))
            WITH CHECK (user_id::text = current_setting('app.user_id', true))
            """
        )

    # utterances are scoped via their parent meeting
    op.execute("ALTER TABLE utterances ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY utterances_user_isolation ON utterances
        USING (EXISTS (SELECT 1 FROM meetings m WHERE m.id = utterances.meeting_id
               AND m.user_id::text = current_setting('app.user_id', true)))
        WITH CHECK (EXISTS (SELECT 1 FROM meetings m WHERE m.id = utterances.meeting_id
               AND m.user_id::text = current_setting('app.user_id', true)))
        """
    )

    # chat_messages ties through meeting
    op.execute("DROP POLICY IF EXISTS chat_messages_user_isolation ON chat_messages")
    op.execute(
        """
        CREATE POLICY chat_messages_user_isolation ON chat_messages
        USING (EXISTS (SELECT 1 FROM meetings m WHERE m.id = chat_messages.meeting_id
               AND m.user_id::text = current_setting('app.user_id', true)))
        WITH CHECK (EXISTS (SELECT 1 FROM meetings m WHERE m.id = chat_messages.meeting_id
               AND m.user_id::text = current_setting('app.user_id', true)))
        """
    )


def downgrade() -> None:
    for table in ("chat_messages", "integrations", "meetings", "utterances"):
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP TRIGGER IF EXISTS utterance_tsv_trigger ON utterances")
    op.execute("DROP FUNCTION IF EXISTS utterance_tsv_update()")
    op.drop_table("audit_log")
    op.drop_table("integrations")
    op.drop_table("usage_ledger")
    op.drop_table("chat_messages")
    op.drop_table("utterances")
    op.drop_table("meetings")
    op.drop_table("users")
