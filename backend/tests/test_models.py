"""Tests for Pydantic model validation."""
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.models import JobCreate, JobResponse, SectionResponse


# ── JobCreate validation ─────────────────────────────────────────

class TestJobCreate:
    def test_valid_job_create(self):
        job = JobCreate(
            jd_url="https://example.com/job",
            jd_text="A" * 60,
        )
        assert job.jd_url == "https://example.com/job"

    def test_empty_url_rejected(self):
        with pytest.raises(ValidationError, match="jd_url"):
            JobCreate(jd_url="", jd_text="A" * 60)

    def test_non_http_url_rejected(self):
        with pytest.raises(ValidationError, match="HTTP"):
            JobCreate(jd_url="ftp://example.com/job", jd_text="A" * 60)

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError, match="jd_text"):
            JobCreate(jd_url="https://example.com/job", jd_text="")

    def test_short_text_rejected(self):
        with pytest.raises(ValidationError, match="50 characters"):
            JobCreate(jd_url="https://example.com/job", jd_text="Too short")

    def test_url_trimmed(self):
        job = JobCreate(
            jd_url="  https://example.com/job  ",
            jd_text="A" * 60,
        )
        assert job.jd_url == "https://example.com/job"


# ── JobResponse validation ───────────────────────────────────────

class TestJobResponse:
    def _base_fields(self, **overrides):
        fields = {
            "id": "abc",
            "company": "Acme",
            "role": "Engineer",
            "date_added": "2026-01-30",
            "pipeline_stage": "queue",
            "extraction_status": "complete",
            "created": "2026-01-30T12:00:00Z",
            "updated": "2026-01-30T12:00:00Z",
        }
        fields.update(overrides)
        return fields

    def test_valid_response(self):
        resp = JobResponse(**self._base_fields())
        assert resp.id == "abc"

    def test_empty_date_added_defaults_to_today(self):
        resp = JobResponse(**self._base_fields(date_added=""))
        assert resp.date_added == date.today()

    def test_none_date_added_defaults_to_today(self):
        resp = JobResponse(**self._base_fields(date_added=None))
        assert resp.date_added == date.today()

    def test_empty_string_optional_fields_become_none(self):
        resp = JobResponse(**self._base_fields(
            date_posted="", score="", hours="", verdict="", jd_cleaned=""
        ))
        assert resp.date_posted is None
        assert resp.score is None
        assert resp.hours is None
        assert resp.verdict is None
        assert resp.jd_cleaned is None

    def test_slug_field_present(self):
        resp = JobResponse(**self._base_fields(slug="acme-engineer-2026"))
        assert resp.slug == "acme-engineer-2026"

    def test_slug_field_optional(self):
        resp = JobResponse(**self._base_fields())
        assert resp.slug is None


# ── SectionResponse validation ───────────────────────────────────

class TestSectionResponse:
    def _base_fields(self, **overrides):
        fields = {
            "id": "sec1",
            "job": "job1",
            "section_key": "evidence_cleanup",
            "phase": "analysis",
            "status": "complete",
            "is_locked": False,
            "created": "2026-01-30T12:00:00Z",
            "updated": "2026-01-30T12:00:00Z",
        }
        fields.update(overrides)
        return fields

    def test_valid_section(self):
        s = SectionResponse(**self._base_fields())
        assert s.section_key == "evidence_cleanup"

    def test_empty_string_optional_fields(self):
        s = SectionResponse(**self._base_fields(
            content_md="", model="", error_message="",
            tokens_used="", generation_time_ms=""
        ))
        assert s.content_md is None
        assert s.model is None
        assert s.error_message is None
        assert s.tokens_used is None
        assert s.generation_time_ms is None

    def test_missing_is_locked_fails(self):
        fields = self._base_fields()
        del fields["is_locked"]
        with pytest.raises(ValidationError):
            SectionResponse(**fields)
