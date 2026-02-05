"""Tests for JD fetcher service."""
from __future__ import annotations

import pytest

from app.services.jd_fetcher import (
    _calculate_section_word_counts,
    _count_html_words,
    _format_error_message,
    _validate_completeness,
    SectionHeading,
)


# ── HTML word counting tests ────────────────────────────────────


def test_count_html_words_simple():
    """Count words from simple HTML."""
    html = "<html><body><p>Hello world this is a test</p></body></html>"
    count = _count_html_words(html)
    assert count == 6


def test_count_html_words_with_tags():
    """Count words while ignoring HTML tags."""
    html = "<div><h1>Title</h1><p>Some <strong>bold</strong> text</p></div>"
    count = _count_html_words(html)
    assert count == 4  # Title, Some, bold, text


def test_count_html_words_strips_scripts():
    """Script tags and content should be stripped."""
    html = "<html><script>function foo() { return 1; }</script><p>Real content</p></html>"
    count = _count_html_words(html)
    assert count == 2  # Real, content


def test_count_html_words_strips_styles():
    """Style tags and content should be stripped."""
    html = "<html><style>.foo { color: red; }</style><p>Visible text</p></html>"
    count = _count_html_words(html)
    assert count == 2  # Visible, text


def test_count_html_words_decodes_entities():
    """Common HTML entities should be decoded."""
    html = "<p>Tom &amp; Jerry &lt;friends&gt;</p>"
    # After decoding: "Tom & Jerry <friends>"
    count = _count_html_words(html)
    assert count >= 3  # At least Tom, &, Jerry


# ── Section word count tests ────────────────────────────────────


def test_calculate_section_word_counts_basic():
    """Calculate word counts for multiple sections."""
    jd_text = """About Us
We are a great company with amazing culture.

Responsibilities
Lead technical projects. Mentor junior engineers. Write clean code.

Requirements
5+ years experience. Python expertise. Good communication."""

    headings = ["About Us", "Responsibilities", "Requirements"]
    result = _calculate_section_word_counts(jd_text, headings)

    assert len(result) == 3
    assert result[0].name == "About Us"
    assert result[1].name == "Responsibilities"
    assert result[2].name == "Requirements"
    # Each section should have positive word count
    for section in result:
        assert section.word_count > 0


def test_calculate_section_word_counts_case_insensitive():
    """Headings should be found case-insensitively."""
    jd_text = """ABOUT THE ROLE
This is a senior position.

WHAT YOU'LL DO
Build amazing products."""

    headings = ["About The Role", "What You'll Do"]
    result = _calculate_section_word_counts(jd_text, headings)

    assert len(result) == 2
    assert result[0].name == "About The Role"
    assert result[1].name == "What You'll Do"


def test_calculate_section_word_counts_empty_headings():
    """Empty headings list should return empty result."""
    jd_text = "Some job description text here."
    result = _calculate_section_word_counts(jd_text, [])
    assert result == []


def test_calculate_section_word_counts_missing_headings():
    """Headings not found in text should be skipped."""
    jd_text = """About Us
We are great.

Benefits
Health insurance."""

    headings = ["About Us", "Requirements", "Benefits"]  # Requirements not in text
    result = _calculate_section_word_counts(jd_text, headings)

    assert len(result) == 2
    assert result[0].name == "About Us"
    assert result[1].name == "Benefits"


def test_calculate_section_word_counts_single_heading():
    """Single heading should count all following text."""
    jd_text = """About the Role
This is a long description with many words describing the role in detail."""

    headings = ["About the Role"]
    result = _calculate_section_word_counts(jd_text, headings)

    assert len(result) == 1
    assert result[0].name == "About the Role"
    assert result[0].word_count > 10


# ── Completeness validation tests ────────────────────────────────


def test_validate_completeness_full_content():
    """Full content with high confidence should be marked complete."""
    # Create content with 300+ words
    jd_text = "Senior Software Engineer\n\n" + " ".join(["word"] * 300)
    is_complete, confidence = _validate_completeness(jd_text, True, 0.95)
    assert is_complete is True
    assert confidence == 0.95


def test_validate_completeness_short_content():
    """Short content should be marked incomplete."""
    jd_text = "Software Engineer at ACME"  # ~4 words
    is_complete, confidence = _validate_completeness(jd_text, True, 0.9)
    assert is_complete is False
    assert confidence <= 0.6


def test_validate_completeness_with_truncation():
    """Content with truncation markers should be marked incomplete."""
    jd_text = "Great opportunity... Read more to see full description\n\n" + "word " * 100
    is_complete, confidence = _validate_completeness(jd_text, True, 0.9)
    assert is_complete is False
    assert confidence <= 0.7


def test_validate_completeness_with_login_marker():
    """Content with login markers should be marked incomplete."""
    jd_text = "Job requirements:\n\n" + "word " * 100 + "\n\nSign in to apply"
    is_complete, confidence = _validate_completeness(jd_text, True, 0.9)
    assert is_complete is False
    assert confidence <= 0.7


def test_validate_completeness_low_confidence():
    """Low LLM confidence should result in incomplete."""
    jd_text = "Senior Engineer\n\n" + "word " * 100
    is_complete, confidence = _validate_completeness(jd_text, True, 0.5)
    assert is_complete is False
    assert confidence == 0.5


def test_validate_completeness_300_word_threshold():
    """Content just at 300 words should pass threshold."""
    jd_text = "word " * 60  # 60 words = 300 characters approximately
    # More precisely, 300 words
    jd_text = " ".join(["word"] * 300)
    is_complete, confidence = _validate_completeness(jd_text, True, 0.8)
    assert is_complete is True
    assert confidence == 0.8


def test_validate_completeness_299_word_threshold():
    """Content just below 300 words should fail threshold."""
    jd_text = " ".join(["word"] * 299)
    is_complete, confidence = _validate_completeness(jd_text, True, 0.95)
    assert is_complete is False
    assert confidence <= 0.6


# ── Error formatting tests ───────────────────────────────────────


def test_format_error_403_forbidden():
    """403 errors should suggest manual entry."""
    error = Exception("403 Forbidden")
    message = _format_error_message(error)
    assert "automated access" in message
    assert "paste" in message


def test_format_error_404_not_found():
    """404 errors should suggest URL might be expired."""
    error = Exception("404 Not Found")
    message = _format_error_message(error)
    assert "404" in message
    assert "expired" in message or "incorrect" in message


def test_format_error_timeout():
    """Timeout errors should suggest retry or manual entry."""
    error = Exception("timeout")
    message = _format_error_message(error)
    assert "timed out" in message.lower() or "timeout" in message.lower()
    assert "paste" in message


def test_format_error_login_required():
    """Login-required errors should explain limitation."""
    error = Exception("authentication required - sign in")
    message = _format_error_message(error)
    assert "login" in message or "authentication" in message
    assert "paste" in message


def test_format_error_playwright_needed():
    """Playwright errors should explain JavaScript rendering needed."""
    error = Exception("Playwright rendering required")
    message = _format_error_message(error)
    assert "javascript" in message.lower() or "playwright" in message.lower()


def test_format_error_generic():
    """Generic errors should provide truncated message."""
    error = Exception("Some random error message that is very long")
    message = _format_error_message(error)
    assert "Failed to fetch" in message
    assert "paste" in message


# ── Integration test stubs (these would use mocked fetching) ──────


@pytest.mark.asyncio
async def test_fetch_valid_url_success():
    """
    Integration test: Fetch from valid public job posting.
    Requires network access and may be flaky in CI.
    """
    # This test would use a real public job URL
    # For now, skip to avoid network dependency
    pytest.skip("Requires network access and real job URL")


@pytest.mark.asyncio
async def test_fetch_invalid_url():
    """Fetch from invalid URL should return failure."""
    # This would call fetch_jd_from_url with invalid URL
    pytest.skip("Requires integration setup")


@pytest.mark.asyncio
async def test_fetch_401_authentication():
    """Fetch from auth-required URL should return helpful error."""
    # This would test LinkedIn-like auth wall
    pytest.skip("Requires integration setup")
