"""Tests for pipeline executor internals."""
import re
from unittest.mock import MagicMock, patch

from tests.conftest import _make_section_record


def test_extract_verdict_score():
    """Extracts score from verdict content."""
    from app.services.pipeline_executor import _extract_verdict_metadata

    mock_pb = MagicMock()
    with patch("app.services.pipeline_executor.pb", mock_pb):
        _extract_verdict_metadata("job1", "Total Score: 72/100")
        mock_pb.collection().update.assert_called_once()
        call_data = mock_pb.collection().update.call_args[0][1]
        assert call_data["score"] == 72


def test_extract_verdict_hours_range():
    """Extracts hours from a range (takes midpoint)."""
    from app.services.pipeline_executor import _extract_verdict_metadata

    mock_pb = MagicMock()
    with patch("app.services.pipeline_executor.pb", mock_pb):
        _extract_verdict_metadata("job1", "Expected Hours: 40-50")
        call_data = mock_pb.collection().update.call_args[0][1]
        assert call_data["hours"] == 45


def test_extract_verdict_hours_single():
    """Extracts hours from a single value."""
    from app.services.pipeline_executor import _extract_verdict_metadata

    mock_pb = MagicMock()
    with patch("app.services.pipeline_executor.pb", mock_pb):
        _extract_verdict_metadata("job1", "Expected Hours: 35")
        call_data = mock_pb.collection().update.call_args[0][1]
        assert call_data["hours"] == 35


def test_extract_verdict_string():
    """Extracts verdict string (STRONG PURSUE, etc)."""
    from app.services.pipeline_executor import _extract_verdict_metadata

    for verdict in ["STRONG PURSUE", "PURSUE", "PASS", "HARD PASS"]:
        mock_pb = MagicMock()
        with patch("app.services.pipeline_executor.pb", mock_pb):
            _extract_verdict_metadata("job1", f"Verdict: {verdict}")
            call_data = mock_pb.collection().update.call_args[0][1]
            assert call_data["verdict"] == verdict


def test_extract_verdict_no_match():
    """No update when verdict content has no recognized patterns."""
    from app.services.pipeline_executor import _extract_verdict_metadata

    mock_pb = MagicMock()
    with patch("app.services.pipeline_executor.pb", mock_pb):
        _extract_verdict_metadata("job1", "Nothing useful here")
        mock_pb.collection().update.assert_not_called()


def test_update_section_status_includes_is_locked():
    """_update_section_status passes is_locked: False."""
    from app.services.pipeline_executor import _update_section_status
    from app.sections.config import SectionDef

    sd = SectionDef("test_key", "Test", 1, [], "analysis")

    mock_upsert = MagicMock()
    with patch("app.services.pipeline_executor.upsert_section", mock_upsert):
        _update_section_status("job1", sd, "running")

    call_data = mock_upsert.call_args[0][2]
    assert call_data["is_locked"] is False


def test_save_section_result_includes_is_locked():
    """_save_section_result passes is_locked: False."""
    from app.services.pipeline_executor import _save_section_result
    from app.sections.config import SectionDef

    sd = SectionDef("test_key", "Test", 1, [], "analysis")

    class FakeResult:
        content_md = "# Result"
        model = "test-model"
        tokens_used = 100
        generation_time_ms = 500

    mock_upsert = MagicMock()
    with patch("app.services.pipeline_executor.upsert_section", mock_upsert):
        _save_section_result("job1", sd, FakeResult())

    call_data = mock_upsert.call_args[0][2]
    assert call_data["is_locked"] is False
    assert call_data["content_md"] == "# Result"


def test_load_completed_sections():
    """_load_completed_sections returns {key: content} dict."""
    from app.services.pipeline_executor import _load_completed_sections

    mock_pb = MagicMock()
    mock_pb.collection().get_full_list.return_value = [
        _make_section_record(section_key="evidence_cleanup", content_md="content1"),
        _make_section_record(section_key="gate_check", content_md="content2"),
    ]

    with patch("app.services.pipeline_executor.pb", mock_pb):
        result = _load_completed_sections("job1")

    assert result["evidence_cleanup"] == "content1"
    assert result["gate_check"] == "content2"


def test_get_locked_keys():
    """_get_locked_keys returns set of locked section keys."""
    from app.services.pipeline_executor import _get_locked_keys

    mock_pb = MagicMock()
    mock_pb.collection().get_full_list.return_value = [
        _make_section_record(section_key="evidence_cleanup", is_locked=True),
    ]

    with patch("app.services.pipeline_executor.pb", mock_pb):
        result = _get_locked_keys("job1")

    assert result == {"evidence_cleanup"}
