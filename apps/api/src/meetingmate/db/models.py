"""SQLAlchemy ORM models matching the schema documented in the build prompt."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    preferred_source_lang: Mapped[str] = mapped_column(String(8), default="ja")
    preferred_target_lang: Mapped[str] = mapped_column(String(8), default="en")
    plan: Mapped[str] = mapped_column(String, nullable=False, default="free")
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    pinned_vocabulary: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    consent_recording_ack_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meetings: Mapped[list[Meeting]] = relationship(back_populates="user")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_s: Mapped[int] = mapped_column(Integer, default=0)
    source_language: Mapped[str] = mapped_column(String(8), default="ja")
    target_language: Mapped[str] = mapped_column(String(8), default="en")
    status: Mapped[str] = mapped_column(String, default="recording")
    template: Mapped[str] = mapped_column(String, default="default")
    google_meet_code: Mapped[str | None] = mapped_column(String, nullable=True)
    participant_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decisions: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    action_items: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    open_questions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    glossary: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    stt_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    llm_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=True)
    transcript_s3_key: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="meetings")
    utterances: Mapped[list[Utterance]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="Utterance.start_ms"
    )
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class Utterance(Base):
    __tablename__ = "utterances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    speaker_id: Mapped[str] = mapped_column(String, default="0")
    speaker_name: Mapped[str | None] = mapped_column(String, nullable=True)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_text_tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    translated_text_tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped[Meeting] = relationship(back_populates="utterances")

    __table_args__ = (
        Index("utterances_meeting_idx", "meeting_id", "start_ms"),
        Index("utterances_orig_tsv", "original_text_tsv", postgresql_using="gin"),
        Index("utterances_trans_tsv", "translated_text_tsv", postgresql_using="gin"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped[Meeting] = relationship(back_populates="chat_messages")


class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    minutes_transcribed: Mapped[int] = mapped_column(Integer, default=0)
    llm_tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    llm_tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    stt_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    llm_cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_usage_user_date"),)


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    credentials_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
