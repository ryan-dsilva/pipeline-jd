"""Tests for database.upsert_section."""
from unittest.mock import MagicMock, patch

from tests.conftest import _make_section_record


def test_upsert_creates_when_not_found():
    """When section doesn't exist, upsert creates it."""
    mock_pb = MagicMock()
    collection = MagicMock()
    mock_pb.collection.return_value = collection

    collection.get_first_list_item.side_effect = Exception("Not found")
    collection.create.return_value = _make_section_record()

    with patch("app.database.pb", mock_pb):
        from app.database import upsert_section
        result = upsert_section("job1", "evidence_cleanup", {
            "phase": "analysis", "status": "running", "is_locked": False,
        })

    assert result["section_key"] == "evidence_cleanup"
    collection.create.assert_called_once()
    # Verify job and section_key were added to data
    call_data = collection.create.call_args[0][0]
    assert call_data["job"] == "job1"
    assert call_data["section_key"] == "evidence_cleanup"


def test_upsert_updates_when_found():
    """When section exists, upsert updates it."""
    mock_pb = MagicMock()
    collection = MagicMock()
    mock_pb.collection.return_value = collection

    existing = _make_section_record(id="existing_id")
    collection.get_first_list_item.return_value = existing
    collection.update.return_value = _make_section_record(status="running")

    with patch("app.database.pb", mock_pb):
        from app.database import upsert_section
        result = upsert_section("job1", "evidence_cleanup", {
            "phase": "analysis", "status": "running", "is_locked": False,
        })

    collection.update.assert_called_once()
    assert result["status"] == "running"


def test_upsert_returns_dict():
    """Upsert returns a plain dict, not a record object."""
    mock_pb = MagicMock()
    collection = MagicMock()
    mock_pb.collection.return_value = collection

    collection.get_first_list_item.side_effect = Exception("Not found")
    collection.create.return_value = _make_section_record()

    with patch("app.database.pb", mock_pb):
        from app.database import upsert_section
        result = upsert_section("job1", "evidence_cleanup", {
            "phase": "analysis", "status": "complete", "is_locked": False,
        })

    assert isinstance(result, dict)
    assert "id" in result
