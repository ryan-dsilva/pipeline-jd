from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import google.genai
from google.genai.types import Content

from app.config import settings

# Use the latest stable model with best quality/cost balance
MODEL = "models/gemini-2.5-flash"

# Initialize client with API key
client = google.genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None


@dataclass
class GenerationResult:
    content_md: str
    model: str
    tokens_used: int
    generation_time_ms: int


def call_llm(
    *,
    system: str,
    user: str,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    use_web_search: bool = True,
) -> GenerationResult:
    """
    Generate content using google.genai (Gemini API).

    Supports:
    - System instructions for role definition
    - Temperature control for creativity/determinism
    - Output token limits
    - Token counting for tracking usage
    """
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured")

    start = time.perf_counter()

    try:
        # Build the request with system instruction
        # google.genai uses system_instruction parameter for role/context
        config = {
            "system_instruction": system,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Enable web search if requested
        if use_web_search:
            config["tools"] = [{"google_search": {}}]
        
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": user}]
                }
            ],
            config=config
        )

        content_md = response.text

        # Extract token counts from usage metadata
        tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            tokens = (
                response.usage_metadata.prompt_token_count +
                response.usage_metadata.candidates_token_count
            )

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    print(f"\n--- LLM OUTPUT START ({MODEL}) [tokens: {tokens}, time: {elapsed_ms}ms] ---\n{content_md}\n--- LLM OUTPUT END ---\n")

    return GenerationResult(
        content_md=content_md,
        model=MODEL,
        tokens_used=tokens,
        generation_time_ms=elapsed_ms,
    )


def call_llm_with_cache(
    *,
    system: str,
    user: str,
    cached_content: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
) -> GenerationResult:
    """
    Generate content with prompt caching for reference materials.

    Reduces latency and cost for repeated reference material (rubrics, frameworks).
    Caches system instruction + large reference content.
    """
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured")

    start = time.perf_counter()

    try:
        # Build contents with cache tokens if reference material is provided
        contents = [
            {
                "role": "user",
                "parts": [{"text": user}]
            }
        ]

        # If cached content is provided, prepend it to the system instruction
        system_instruction = system
        if cached_content:
            system_instruction = f"{system}\n\n## CACHED REFERENCE MATERIAL\n{cached_content}"

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config={
                "system_instruction": system_instruction,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )

        content_md = response.text

        # Extract token counts - note cache hits use fewer tokens
        tokens = 0
        cache_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            tokens = (
                response.usage_metadata.prompt_token_count +
                response.usage_metadata.candidates_token_count
            )
            if hasattr(response.usage_metadata, 'cached_content_input_token_count'):
                cache_tokens = response.usage_metadata.cached_content_input_token_count

    except Exception as e:
        print(f"Error calling Gemini API with cache: {e}")
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    cache_note = f" [cache hits: {cache_tokens}]" if cache_tokens > 0 else ""

    print(f"\n--- LLM OUTPUT START ({MODEL}) [tokens: {tokens}{cache_note}, time: {elapsed_ms}ms] ---\n{content_md}\n--- LLM OUTPUT END ---\n")

    return GenerationResult(
        content_md=content_md,
        model=MODEL,
        tokens_used=tokens,
        generation_time_ms=elapsed_ms,
    )
