from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


# ── Pipeline stages ──────────────────────────────────────────────
PIPELINE_STAGES = [
    "queue",
    "analyzing",
    "analyzed",
    "cover_letter_gen",
    "ready",
    "applied",
    "ignored",
]

VERDICTS = ["STRONG PURSUE", "PURSUE", "PASS", "HARD PASS"]


# ── Jobs ─────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    jd_url: str
    jd_text: str

    @field_validator("jd_url", mode="before")
    @classmethod
    def validate_jd_url(cls, v):
        if not v or not v.strip():
            raise ValueError("jd_url must not be empty")
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("jd_url must be a valid HTTP(S) URL")
        return v

    @field_validator("jd_text", mode="before")
    @classmethod
    def validate_jd_text(cls, v):
        if not v or not v.strip():
            raise ValueError("jd_text must not be empty")
        if len(v.strip()) < 50:
            raise ValueError("jd_text must be at least 50 characters")
        return v


class JobStageUpdate(BaseModel):
    stage: str


class JobUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    company: str
    role: str
    slug: Optional[str] = None
    jd_url: Optional[str] = None
    jd_text: Optional[str] = None
    jd_cleaned: Optional[str] = None
    date_added: date
    date_posted: Optional[date] = None
    pipeline_stage: str
    score: Optional[int] = None
    hours: Optional[int] = None
    verdict: Optional[str] = None
    extraction_status: str = "pending"
    created: datetime
    updated: datetime

    @model_validator(mode="before")
    @classmethod
    def fill_missing_system_fields(cls, values):
        if isinstance(values, dict):
            if not values.get("extraction_status"):
                values["extraction_status"] = "pending"
            if not values.get("created"):
                values["created"] = datetime.utcnow().isoformat()
            if not values.get("updated"):
                values["updated"] = values.get("created") or datetime.utcnow().isoformat()
        return values

    @field_validator("date_added", mode="before")
    @classmethod
    def empty_date_added_to_today(cls, v):
        if v == "" or v is None:
            return date.today()
        return v

    @field_validator(
        "date_posted", "score", "hours", "verdict", "jd_cleaned", mode="before"
    )
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


class JobDetailResponse(JobResponse):
    sections: list[SectionResponse] = []


# ── Sections ─────────────────────────────────────────────────────

class SectionResponse(BaseModel):
    id: str
    job: str
    section_key: str
    phase: str
    status: str
    content_md: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    is_locked: bool
    created: datetime
    updated: datetime

    @field_validator(
        "content_md", "model", "error_message", mode="before"
    )
    @classmethod
    def empty_str_to_none_section(cls, v):
        if v == "":
            return None
        return v

    @field_validator("tokens_used", "generation_time_ms", mode="before")
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "":
            return None
        return v


class SectionUpdate(BaseModel):
    content_md: str


class SectionLockToggle(BaseModel):
    is_locked: bool


# ── Section definitions (returned to frontend) ──────────────────

class SectionDefinitionResponse(BaseModel):
    key: str
    label: str
    order: int
    depends_on: list[str]
    phase: str


# ── Pipeline ─────────────────────────────────────────────────────

class PipelineEvent(BaseModel):
    """SSE event sent during pipeline execution."""
    section_key: str
    status: str  # running | complete | failed
    content_md: Optional[str] = None
    error_message: Optional[str] = None


# ── Chat ─────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class JDExtractResponse(BaseModel):
    company: str
    role: str


# Rebuild forward refs for JobDetailResponse → SectionResponse
JobDetailResponse.model_rebuild()
