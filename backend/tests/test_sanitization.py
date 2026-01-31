"""Tests for PocketBase filter value sanitization."""
import pytest

from app.database import sanitize_pb_value


class TestSanitizePbValue:
    def test_plain_string_unchanged(self):
        assert sanitize_pb_value("hello") == "hello"

    def test_double_quotes_escaped(self):
        assert sanitize_pb_value('say "hello"') == 'say \\"hello\\"'

    def test_backslash_escaped(self):
        assert sanitize_pb_value("back\\slash") == "back\\\\slash"

    def test_backslash_before_quote(self):
        """Backslashes are escaped first, then quotes."""
        assert sanitize_pb_value('a\\"b') == 'a\\\\\\"b'

    def test_url_with_query_params(self):
        url = "https://example.com/job?id=1&name=test"
        assert sanitize_pb_value(url) == url  # No special chars to escape

    def test_url_with_quotes(self):
        url = 'https://example.com/job?q="engineer"'
        result = sanitize_pb_value(url)
        assert '\\"' in result
        assert result == 'https://example.com/job?q=\\"engineer\\"'
