"""Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateMeetingRequest(BaseModel):
    title: str | None = None
    source_language: str = "ja"
    target_language: str = "en"
    google_meet_code: str | None = None
    template: str = "default"


class CreateMeetingResponse(BaseModel):
    meeting_id: uuid.UUID
    ws_url: str
    ws_subprotocol: str = "meetingmate.v1"


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_s: int
    source_language: str
    target_language: str
    status: str
    template: str
    participant_names: list[str]
    summary: str | None
    decisions: list[dict]
    action_items: list[dict]
    open_questions: list[str] = Field(default_factory=list)
    glossary: list[dict]
    stt_cost_cents: int
    llm_cost_cents: int
    created_at: datetime


class UtteranceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    speaker_id: str
    speaker_name: str | None
    start_ms: int
    end_ms: int
    original_text: str
    translated_text: str | None
    confidence: float | None
    is_important: bool


class MeetingListResponse(BaseModel):
    items: list[MeetingOut]
    next_cursor: str | None = None


class UtteranceListResponse(BaseModel):
    items: list[UtteranceOut]
    next_cursor: str | None = None


class VocabularyItem(BaseModel):
    term: str
    translation: str | None = None
    pronunciation: str | None = None


class VocabularyListResponse(BaseModel):
    items: list[VocabularyItem]


class UsageResponse(BaseModel):
    minutes_today: int
    minutes_limit: int
    plan: str
    cost_usd_today: float


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class SearchResponse(BaseModel):
    items: list[dict]
