"""Tests for extraction utility."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.extraction import ExtractionError, extract_company_role


@pytest.mark.asyncio
async def test_extract_parses_valid_json():
    """Extracts company and role from valid JSON response."""
    mock_response = Mock()
    mock_block = Mock()
    mock_block.type = "text"
    mock_block.text = '{"company": "Test Corp", "role": "Engineer"}'
    mock_response.content = [mock_block]

    with patch("app.extraction.client.messages.create", return_value=mock_response):
        result = await extract_company_role("Sample JD text")
        assert result == {"company": "Test Corp", "role": "Engineer"}


@pytest.mark.asyncio
async def test_extract_raises_on_invalid_json():
    """Raises ExtractionError on invalid JSON response."""
    mock_response = Mock()
    mock_block = Mock()
    mock_block.type = "text"
    mock_block.text = "not valid json"
    mock_response.content = [mock_block]

    with patch("app.extraction.client.messages.create", return_value=mock_response):
        with pytest.raises(ExtractionError, match="JSON"):
            await extract_company_role("Sample JD text")


@pytest.mark.asyncio
async def test_extract_raises_on_missing_fields():
    """Raises ExtractionError when response JSON is missing required fields."""
    mock_response = Mock()
    mock_block = Mock()
    mock_block.type = "text"
    mock_block.text = '{"company": "Test Corp"}'
    mock_response.content = [mock_block]

    with patch("app.extraction.client.messages.create", return_value=mock_response):
        with pytest.raises(ExtractionError, match="Invalid"):
            await extract_company_role("Sample JD text")


@pytest.mark.asyncio
async def test_extract_raises_on_api_error():
    """Raises ExtractionError when API call fails."""
    with patch(
        "app.extraction.client.messages.create",
        side_effect=Exception("API error"),
    ):
        with pytest.raises(ExtractionError, match="Extraction failed"):
            await extract_company_role("Sample JD text")


@pytest.mark.anthropic_api
@pytest.mark.asyncio
async def test_extract_real_api():
    """Integration test that calls the real Claude API.

    WARNING: This test costs real money (~$0.01).
    Run with: pytest -m anthropic_api
    """
    jd_text = """
    Software Engineer at Google

    Google is looking for a Software Engineer to join our Cloud team.
    You will design and build scalable systems.

    Requirements:
    - 3+ years of experience in software development
    - Proficiency in Python, Java, or Go
    - Experience with distributed systems
    """
    result = await extract_company_role(jd_text)
    assert "company" in result
    assert "role" in result
    # The model should extract "Google" as company
    assert "google" in result["company"].lower()
