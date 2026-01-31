"""Test fixtures and mocks for backend tests."""
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi.testclient import TestClient


# ── Mock record helpers ──────────────────────────────────────────

def _make_mock_record(**fields):
    """Create a mock PocketBase record with fields accessible as attributes
    and via __dict__ (so record_to_dict works correctly on mocks)."""
    record = MagicMock()
    # Set each field as an attribute
    for k, v in fields.items():
        setattr(record, k, v)
    # Ensure __dict__ contains the fields (for record_to_dict's __dict__ path)
    record.__dict__.update(fields)
    # Disable mapping protocol so record_to_dict doesn't try Mapping path
    record.__contains__ = Mock(return_value=False)
    return record


def _make_job_record(**overrides):
    """Create a mock job record with all required fields pre-populated."""
    defaults = {
        "id": "test_job_id",
        "company": "Acme Corp",
        "role": "Senior Engineer",
        "slug": "acme-corp-senior-engineer-2026-01-30",
        "jd_url": "https://example.com/job",
        "jd_text": "Sample JD text " * 5,  # Ensure >= 50 chars
        "jd_cleaned": "",
        "date_added": "2026-01-30",
        "date_posted": "",
        "pipeline_stage": "queue",
        "score": "",
        "hours": "",
        "verdict": "",
        "extraction_status": "complete",
        "created": "2026-01-30T12:00:00.000Z",
        "updated": "2026-01-30T12:00:00.000Z",
    }
    defaults.update(overrides)
    return _make_mock_record(**defaults)


def _make_section_record(**overrides):
    """Create a mock section record with all required fields pre-populated."""
    defaults = {
        "id": "test_section_id",
        "job": "test_job_id",
        "section_key": "evidence_cleanup",
        "phase": "analysis",
        "status": "complete",
        "content_md": "# Test Content\nSome markdown content here.",
        "model": "claude-haiku-4-5",
        "tokens_used": 500,
        "generation_time_ms": 1200,
        "error_message": "",
        "is_locked": False,
        "created": "2026-01-30T12:00:00.000Z",
        "updated": "2026-01-30T12:00:00.000Z",
    }
    defaults.update(overrides)
    return _make_mock_record(**defaults)


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_pb():
    """Mock PocketBase client — patches at every import site so the mock
    actually reaches router code (each module binds `pb` at import time
    via `from app.database import pb`)."""
    mock = MagicMock()

    # Default collection mock
    collection_mock = MagicMock()
    mock.collection.return_value = collection_mock

    # Default behaviors
    collection_mock.create.return_value = _make_job_record(
        company="", role="", extraction_status="pending"
    )
    collection_mock.get_one.return_value = _make_job_record()
    collection_mock.update.return_value = _make_job_record()
    collection_mock.get_full_list.return_value = []

    # get_first_list_item raises by default (simulating "not found")
    collection_mock.get_first_list_item.side_effect = Exception("Not found")

    patches = [
        patch("app.database.pb", mock),
        patch("app.routers.jobs.pb", mock),
        patch("app.routers.sections.pb", mock),
        patch("app.routers.pipeline.pb", mock),
        patch("app.routers.chat.pb", mock),
        patch("app.services.pipeline_executor.pb", mock),
    ]

    for p in patches:
        p.start()

    yield mock

    for p in patches:
        p.stop()


@pytest.fixture
def mock_extraction():
    """Mock extraction utility — patches at the router import site and uses
    AsyncMock since extract_company_role is async."""
    with patch("app.routers.jobs.extract_company_role", new_callable=AsyncMock) as mock:
        mock.return_value = {"company": "Acme Corp", "role": "Senior Engineer"}
        yield mock


@pytest.fixture
def client(mock_pb):
    """FastAPI test client."""
    from app.main import app
    return TestClient(app)
