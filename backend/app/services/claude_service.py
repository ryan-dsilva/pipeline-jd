from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import anthropic

from app.config import settings

MODEL = "claude-haiku-4-5"

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


@dataclass
class GenerationResult:
    content_md: str
    model: str
    tokens_used: int
    generation_time_ms: int


def call_claude(
    *,
    system: str,
    user: str,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    use_web_search: bool = False,
) -> GenerationResult:
    """Synchronous Claude call with timing and token tracking."""
    tools = []
    if use_web_search:
        tools.append({"type": "web_search_20250305", "name": "web_search"})

    start = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=tools if tools else anthropic.NOT_GIVEN,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    content_md = extract_text(response)
    tokens = response.usage.input_tokens + response.usage.output_tokens

    return GenerationResult(
        content_md=content_md,
        model=MODEL,
        tokens_used=tokens,
        generation_time_ms=elapsed_ms,
    )


def extract_text(response: anthropic.types.Message) -> str:
    """Pull markdown text from a Claude response, skipping tool-use blocks."""
    parts: list[str] = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n\n".join(parts).strip()
