"""Tests for job creation and extraction."""
import pytest
from unittest.mock import AsyncMock, Mock

from tests.conftest import _make_job_record


def test_create_job_saves_and_extracts(client, mock_pb, mock_extraction):
    """Job is created and extraction runs successfully."""
    # After extraction, get_one returns the fully-populated job
    mock_pb.collection().get_one.return_value = _make_job_record()

    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "https://example.com/job",
            "jd_text": "Looking for a Senior Engineer at Acme Corp. " * 3,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test_job_id"
    assert data["company"] == "Acme Corp"
    assert data["role"] == "Senior Engineer"
    assert data["extraction_status"] == "complete"

    # Verify extraction was called
    mock_extraction.assert_called_once()


def test_create_job_extraction_failure_still_saves(client, mock_pb, mock_extraction):
    """Job is created even if extraction fails."""
    # Make extraction fail
    mock_extraction.side_effect = Exception("Extraction error")

    # After failure, get_one returns job with failed status
    mock_pb.collection().get_one.return_value = _make_job_record(
        company="", role="", extraction_status="failed"
    )

    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "https://example.com/job",
            "jd_text": "Some job text that is long enough to pass the 50 char minimum validator.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["extraction_status"] == "failed"
    assert data["company"] == ""
    assert data["role"] == ""


def test_create_job_duplicate_url_rejected(client, mock_pb):
    """Cannot create job with duplicate URL."""
    # Mock get_first_list_item to return existing job (no exception = found)
    existing_job = Mock(id="existing_job_id")
    mock_pb.collection().get_first_list_item.side_effect = None
    mock_pb.collection().get_first_list_item.return_value = existing_job

    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "https://example.com/job",
            "jd_text": "Some job text that is long enough to pass the 50 char minimum validator.",
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_job_missing_url_rejected(client):
    """Cannot create job without URL."""
    response = client.post(
        "/api/jobs",
        json={
            "jd_text": "Some job text that is long enough to pass the 50 char minimum validator.",
        },
    )

    assert response.status_code == 422


def test_create_job_missing_text_rejected(client):
    """Cannot create job without text."""
    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "https://example.com/job",
        },
    )

    assert response.status_code == 422


def test_create_job_empty_url_rejected(client):
    """Cannot create job with empty URL."""
    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "",
            "jd_text": "Some job text that is long enough to pass the 50 char minimum validator.",
        },
    )

    assert response.status_code == 422


def test_create_job_short_text_rejected(client):
    """Cannot create job with JD text shorter than 50 chars."""
    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "https://example.com/job",
            "jd_text": "Too short",
        },
    )

    assert response.status_code == 422


def test_create_job_invalid_url_rejected(client):
    """Cannot create job with non-HTTP URL."""
    response = client.post(
        "/api/jobs",
        json={
            "jd_url": "not-a-valid-url",
            "jd_text": "Some job text that is long enough to pass the 50 char minimum validator.",
        },
    )

    assert response.status_code == 422


def test_reextract_job(client, mock_pb, mock_extraction):
    """Re-extraction updates company and role."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().update.return_value = _make_job_record()

    response = client.post("/api/jobs/test_job_id/extract")

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Acme Corp"
    assert data["role"] == "Senior Engineer"
    assert data["extraction_status"] == "complete"

    mock_extraction.assert_called_once()


def test_reextract_idempotent(client, mock_pb, mock_extraction):
    """Re-extraction can be run multiple times."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().update.return_value = _make_job_record()

    response1 = client.post("/api/jobs/test_job_id/extract")
    assert response1.status_code == 200

    response2 = client.post("/api/jobs/test_job_id/extract")
    assert response2.status_code == 200

    assert mock_extraction.call_count == 2


def test_update_job_company_role(client, mock_pb):
    """PATCH updates company and role."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().update.return_value = _make_job_record(
        company="New Company", role="New Role"
    )

    response = client.patch(
        "/api/jobs/test_job_id",
        json={"company": "New Company", "role": "New Role"},
    )

    assert response.status_code == 200


def test_list_jobs(client, mock_pb):
    """GET /api/jobs returns list of jobs."""
    mock_pb.collection().get_full_list.return_value = [
        _make_job_record(),
        _make_job_record(id="test_job_id_2", company="Beta Inc"),
    ]

    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    mock_pb.collection().get_full_list.assert_called_once()
    query_params = mock_pb.collection().get_full_list.call_args.kwargs["query_params"]
    assert "filter" not in query_params
    assert query_params["sort"] == "-date_added"


def test_get_job_detail(client, mock_pb):
    """GET /api/jobs/{id} returns job with sections."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().get_full_list.return_value = []

    response = client.get("/api/jobs/test_job_id")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_job_id"
    assert data["sections"] == []


def test_delete_job(client, mock_pb):
    """DELETE /api/jobs/{id} succeeds."""
    response = client.delete("/api/jobs/test_job_id")
    assert response.status_code == 204


def test_update_stage(client, mock_pb):
    """PUT /api/jobs/{id}/stage updates pipeline stage."""
    mock_pb.collection().update.return_value = _make_job_record(
        pipeline_stage="analyzing"
    )

    response = client.put(
        "/api/jobs/test_job_id/stage",
        json={"stage": "analyzing"},
    )
    assert response.status_code == 200
    assert response.json()["pipeline_stage"] == "analyzing"


def test_update_stage_invalid(client, mock_pb):
    """PUT /api/jobs/{id}/stage rejects invalid stages."""
    response = client.put(
        "/api/jobs/test_job_id/stage",
        json={"stage": "invalid_stage"},
    )
    assert response.status_code == 400
