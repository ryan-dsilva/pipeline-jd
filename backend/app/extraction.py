"""JD extraction utility using Claude Haiku 4."""
from __future__ import annotations

import asyncio
import re

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = "claude-haiku-4-5"


class ExtractionError(Exception):
    """Raised when JD extraction fails."""


class ExtractionResult(BaseModel):
    """Structured extraction result for company and role."""

    company: str
    role: str


def _extract_json_object(text: str) -> str:
    """Extract the first JSON object substring from text."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ExtractionError("No JSON object found in extraction response")
    return match.group(0)


def _model_to_dict(result: ExtractionResult) -> dict:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result.dict()


async def extract_company_role(jd_text: str) -> dict:
    """
    Extract company name and role title from job description text.

    Args:
        jd_text: The full job description text

    Returns:
        Dict with 'company' and 'role' keys

    Raises:
        ExtractionError: If extraction fails or response is invalid
    """
    system_prompt = """Extract company and role as a JSON object that matches this schema:
{"company": "string", "role": "string"}

Return ONLY a single JSON object, no markdown, no extra keys, no trailing text.

Rules:
- company: exact company name as written in the job description
- role: full role title
- If either is missing, set it to "Unknown"
- Strings only (no null/arrays/objects)"""

    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model=MODEL,
            max_tokens=500,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": jd_text}],
        )

        # Extract text from response
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        # Parse and validate JSON using pydantic
        json_payload = _extract_json_object(text_content.strip())
        try:
            result = ExtractionResult.model_validate_json(json_payload)
        except AttributeError:
            result = ExtractionResult.parse_raw(json_payload)

        return _model_to_dict(result)

    except ExtractionError:
        raise
    except ValidationError as e:
        raise ExtractionError(f"Invalid extraction response: {e}") from e
    except Exception as e:
        raise ExtractionError(f"Extraction failed: {e}") from e
