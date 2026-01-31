"""Tests for record_to_dict conversion logic."""
from unittest.mock import MagicMock, Mock

from app.database import record_to_dict


def test_plain_object_with_attributes():
    """Converts an object with public attributes to dict."""
    record = MagicMock()
    record.id = "abc123"
    record.company = "Acme"
    record.created = "2026-01-01T00:00:00Z"
    record.updated = "2026-01-01T00:00:00Z"
    record.__dict__.update({
        "id": "abc123", "company": "Acme",
        "created": "2026-01-01T00:00:00Z", "updated": "2026-01-01T00:00:00Z",
    })

    result = record_to_dict(record)
    assert result["id"] == "abc123"
    assert result["company"] == "Acme"


def test_dict_record():
    """Converts a plain dict (Mapping) to dict."""
    record = {"id": "abc", "company": "Test", "created": "2026-01-01T00:00:00Z"}
    result = record_to_dict(record)
    assert result["id"] == "abc"
    assert result["company"] == "Test"


def test_private_attributes_excluded():
    """Private attributes (starting with _) are excluded from __dict__ path."""
    record = MagicMock()
    record.__dict__.update({"_internal": "hidden", "public": "visible"})
    record.public = "visible"

    result = record_to_dict(record)
    assert "_internal" not in result
    assert result["public"] == "visible"


def test_system_fields_via_getattr():
    """System fields are always extracted via getattr even if not in __dict__."""
    class SlotRecord:
        __slots__ = ("id", "created", "updated", "collection_id", "collection_name")

        def __init__(self):
            self.id = "sys123"
            self.created = "2026-01-01T00:00:00Z"
            self.updated = "2026-01-01T00:00:00Z"
            self.collection_id = "col_abc"
            self.collection_name = "jobs"

    record = SlotRecord()

    result = record_to_dict(record)
    assert result["id"] == "sys123"
    assert result["created"] == "2026-01-01T00:00:00Z"
    assert result["collection_id"] == "col_abc"


def test_internal_data_dict():
    """Records with _Record__data (PB SDK name-mangled) are handled."""
    record = MagicMock()
    record._Record__data = {"id": "data123", "company": "DataCo"}
    record.id = "data123"
    record.created = "2026-01-01T00:00:00Z"
    record.updated = "2026-01-01T00:00:00Z"

    result = record_to_dict(record)
    assert result["id"] == "data123"
    assert result["company"] == "DataCo"


def test_empty_record():
    """An empty object returns at least an empty dict."""
    record = object()
    result = record_to_dict(record)
    assert isinstance(result, dict)
