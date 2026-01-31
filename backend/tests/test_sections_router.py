"""Tests for sections router."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from tests.conftest import _make_job_record, _make_section_record


def test_list_sections(client, mock_pb):
    """GET /api/sections/{job_id} returns sections list."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().get_full_list.return_value = [
        _make_section_record(section_key="evidence_cleanup"),
        _make_section_record(id="sec2", section_key="gate_check"),
    ]

    response = client.get("/api/sections/test_job_id")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_sections_job_not_found(client, mock_pb):
    """GET /api/sections/{job_id} returns 404 for missing job."""
    mock_pb.collection().get_one.side_effect = Exception("Not found")

    response = client.get("/api/sections/nonexistent")
    assert response.status_code == 404


def test_get_section(client, mock_pb):
    """GET /api/sections/{job_id}/{key} returns single section."""
    mock_pb.collection().get_first_list_item.side_effect = None
    mock_pb.collection().get_first_list_item.return_value = _make_section_record()

    response = client.get("/api/sections/test_job_id/evidence_cleanup")
    assert response.status_code == 200
    data = response.json()
    assert data["section_key"] == "evidence_cleanup"


def test_get_section_not_found(client, mock_pb):
    """GET /api/sections/{job_id}/{key} returns 404."""
    mock_pb.collection().get_first_list_item.side_effect = Exception("Not found")

    response = client.get("/api/sections/test_job_id/nonexistent")
    assert response.status_code == 404


def test_update_section(client, mock_pb):
    """PUT /api/sections/{job_id}/{key} updates content and locks."""
    mock_pb.collection().get_first_list_item.side_effect = None
    mock_pb.collection().get_first_list_item.return_value = _make_section_record()
    mock_pb.collection().update.return_value = _make_section_record(
        content_md="Updated content", is_locked=True
    )

    response = client.put(
        "/api/sections/test_job_id/evidence_cleanup",
        json={"content_md": "Updated content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_locked"] is True


def test_toggle_lock(client, mock_pb):
    """POST /api/sections/{job_id}/{key}/lock toggles lock."""
    mock_pb.collection().get_first_list_item.side_effect = None
    mock_pb.collection().get_first_list_item.return_value = _make_section_record()
    mock_pb.collection().update.return_value = _make_section_record(is_locked=True)

    response = client.post(
        "/api/sections/test_job_id/evidence_cleanup/lock",
        json={"is_locked": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_locked"] is True


def test_toggle_lock_section_not_found(client, mock_pb):
    """POST lock returns 404 if section doesn't exist."""
    mock_pb.collection().get_first_list_item.side_effect = Exception("Not found")

    response = client.post(
        "/api/sections/test_job_id/evidence_cleanup/lock",
        json={"is_locked": True},
    )
    assert response.status_code == 404


def test_get_section_definitions(client, mock_pb):
    """GET /api/section-definitions returns section definitions."""
    response = client.get("/api/section-definitions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Check structure of first item
    first = data[0]
    assert "key" in first
    assert "label" in first
    assert "order" in first
    assert "depends_on" in first
    assert "phase" in first
