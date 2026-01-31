"""Tests for pipeline router."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import _make_job_record


def test_analyze_job_not_found(client, mock_pb):
    """POST /api/pipeline/{job_id}/analyze returns 404 for missing job."""
    mock_pb.collection().get_one.side_effect = Exception("Not found")

    response = client.post("/api/pipeline/nonexistent/analyze")
    assert response.status_code == 404


def test_cover_letter_job_not_found(client, mock_pb):
    """POST /api/pipeline/{job_id}/cover-letter returns 404 for missing job."""
    mock_pb.collection().get_one.side_effect = Exception("Not found")

    response = client.post("/api/pipeline/nonexistent/cover-letter")
    assert response.status_code == 404


def test_pipeline_status_job_not_found(client, mock_pb):
    """GET /api/pipeline/{job_id}/status returns 404 for missing job."""
    mock_pb.collection().get_one.side_effect = Exception("Not found")

    response = client.get("/api/pipeline/nonexistent/status")
    assert response.status_code == 404


def test_analyze_starts_sse_stream(client, mock_pb):
    """POST /api/pipeline/{job_id}/analyze returns SSE stream."""
    mock_pb.collection().get_one.return_value = _make_job_record()

    from app.models import PipelineEvent

    async def mock_pipeline(job, phase):
        yield PipelineEvent(section_key="evidence_cleanup", status="running")
        yield PipelineEvent(
            section_key="evidence_cleanup",
            status="complete",
            content_md="# Cleaned",
        )

    with patch("app.routers.pipeline.run_pipeline", side_effect=mock_pipeline):
        response = client.post("/api/pipeline/test_job_id/analyze")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "evidence_cleanup" in body
    assert "complete" in body
