"""JD fetching service with intelligent HTML retrieval and extraction."""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from anthropic import AsyncAnthropic

from app.config import settings

# Sites that require JavaScript rendering
JS_REQUIRED_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "myworkdayjobs.com",
    "builtin.com",
    "wellfound.com",
]


@dataclass
class SectionHeading:
    """A detected section heading with word count."""

    name: str
    word_count: int


@dataclass
class FetchResult:
    """Result of JD fetch attempt."""

    success: bool
    jd_text: str | None
    is_complete: bool
    confidence: float
    word_count: int
    html_word_count: int  # Total words in raw HTML (for extraction ratio)
    section_headings: list[SectionHeading]  # Detected sections with word counts
    error_message: str | None
    method_used: str  # "httpx" | "playwright" | "failed"


async def fetch_jd_from_url(url: str) -> FetchResult:
    """
    Intelligently fetch JD content from URL.

    Strategy:
    1. Detect if site requires JavaScript rendering
    2. Use httpx for static sites (fast)
    3. Use Playwright for JS-heavy sites (reliable)
    4. Extract JD text from HTML using Claude
    5. Validate completeness with heuristics
    6. Fallback: Try Playwright if httpx yields too little content

    Args:
        url: Job posting URL

    Returns:
        FetchResult with success status, JD text, completeness, and method used
    """
    requires_js = any(domain in url.lower() for domain in JS_REQUIRED_DOMAINS)

    try:
        # Stage 1: Fetch HTML
        if requires_js:
            html = await _fetch_with_playwright(url)
            method = "playwright"
        else:
            try:
                html = await _fetch_with_httpx(url)
                method = "httpx"
            except Exception:
                # Fallback to Playwright for unexpected JS sites
                html = await _fetch_with_playwright(url)
                method = "playwright"

        # Calculate HTML word count before extraction (for ratio display)
        html_word_count = _count_html_words(html)

        # Stage 2: Extract JD text from HTML
        extraction = await _extract_jd_from_html(html, url)

        # Stage 3: Validate completeness
        is_complete, confidence = _validate_completeness(
            extraction["jd_text"],
            extraction["is_complete"],
            extraction["confidence"],
        )

        word_count = len(extraction["jd_text"].split())

        # Stage 4: Fallback to Playwright if httpx gave insufficient content
        if method == "httpx" and word_count < 200:
            html = await _fetch_with_playwright(url)
            html_word_count = _count_html_words(html)
            extraction = await _extract_jd_from_html(html, url)
            is_complete, confidence = _validate_completeness(
                extraction["jd_text"],
                extraction["is_complete"],
                extraction["confidence"],
            )
            word_count = len(extraction["jd_text"].split())
            method = "playwright"

        # Calculate section word counts from headings
        section_headings = _calculate_section_word_counts(
            extraction["jd_text"],
            extraction.get("section_headings", []),
        )

        return FetchResult(
            success=True,
            jd_text=extraction["jd_text"],
            is_complete=is_complete,
            confidence=confidence,
            word_count=word_count,
            html_word_count=html_word_count,
            section_headings=section_headings,
            error_message=None,
            method_used=method,
        )

    except Exception as e:
        return FetchResult(
            success=False,
            jd_text=None,
            is_complete=False,
            confidence=0.0,
            word_count=0,
            html_word_count=0,
            section_headings=[],
            error_message=_format_error_message(e),
            method_used="failed",
        )


async def _fetch_with_httpx(url: str) -> str:
    """Fetch HTML using httpx (fast, for static sites)."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_with_playwright(url: str) -> str:
    """
    Fetch HTML using Playwright (handles JavaScript rendering).

    Note: This is a placeholder that would integrate with Claude Code's
    Playwright MCP plugin. The actual implementation would use:
    - mcp_playwright.browser_navigate(url)
    - mcp_playwright.browser_wait_for(text=selector)
    - mcp_playwright.browser_snapshot(return_html=True)

    For now, we return a helpful error message if Playwright is needed
    but not available in the synchronous context.
    """
    # This would be called via Playwright MCP in actual implementation
    # For now, attempting to signal that Playwright is needed
    import asyncio

    # Simulate a delay that would occur with Playwright
    await asyncio.sleep(0.1)

    # In production, this would be:
    # 1. Navigate to URL via Playwright
    # 2. Wait for job content selectors to appear
    # 3. Get full rendered HTML

    # Placeholder: Raise error that will be handled gracefully
    raise RuntimeError(
        "Playwright rendering required for this site. "
        "Configure Playwright MCP for full support."
    )


async def _extract_jd_from_html(html: str, url: str) -> dict:
    """
    Extract job description text from HTML using Claude.

    Args:
        html: Raw HTML content from job posting
        url: Original URL (for context)

    Returns:
        Dict with jd_text, is_complete, confidence, section_headings
    """
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_prompt = """Extract the job description text from the provided HTML.

Return a JSON object matching this schema:
{
  "jd_text": "string - the complete job description text",
  "is_complete": "boolean - true if you extracted the full JD",
  "confidence": "number 0.0-1.0 - confidence in completeness",
  "section_headings": ["string array - exact heading text as it appears in the JD"]
}

Rules:
- Extract ONLY the job description content (responsibilities, requirements, benefits, company info)
- Strip all navigation, headers, footers, ads, application forms, and metadata
- Preserve structure (bullet points, sections) but remove HTML tags
- Return plain text, not markdown or HTML
- Set is_complete=false if you see truncation markers, login walls, paywalls, or "Sign in to view"
- Confidence should be 0.0-1.0 where:
  - 0.9-1.0: Full, untruncated JD with clear structure
  - 0.7-0.9: Mostly complete with minor missing sections
  - 0.4-0.7: Partial content or unclear completeness
  - 0.0-0.4: Very little content or severely truncated
- For section_headings: Return the EXACT text of each section heading as it appears in the JD
  - Common headings: "About Us", "Responsibilities", "Requirements", "Qualifications", "Benefits", "What You'll Do", etc.
  - Only include actual headings, not paragraph text
  - Return them in the order they appear in the document"""

    # Limit HTML to first 100KB to avoid token overload
    html_preview = html[:100000]

    user_prompt = f"Extract the job description from this HTML:\n\n{html_preview}"

    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4000,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract JSON from response
    text_content = "".join(
        block.text for block in response.content if block.type == "text"
    )

    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON found in extraction response")

    import json

    return json.loads(json_match.group(0))


def _count_html_words(html: str) -> int:
    """
    Count approximate words in HTML by stripping tags and counting.

    Args:
        html: Raw HTML content

    Returns:
        Approximate word count from visible text
    """
    # Remove script and style tags with their content
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    # Split on whitespace and count
    words = text.split()
    return len(words)


def _calculate_section_word_counts(
    jd_text: str, headings: list[str]
) -> list[SectionHeading]:
    """
    Calculate word counts for each section based on heading positions.

    Uses exact substring search to find headings in the text, then counts
    words between consecutive headings.

    Args:
        jd_text: The extracted JD text
        headings: List of section heading strings (exact text)

    Returns:
        List of SectionHeading with name and word_count
    """
    if not headings or not jd_text:
        return []

    # Find positions of each heading in the text
    heading_positions: list[tuple[int, str]] = []
    for heading in headings:
        # Try exact match first
        pos = jd_text.find(heading)
        if pos == -1:
            # Try case-insensitive search
            lower_text = jd_text.lower()
            lower_heading = heading.lower()
            pos = lower_text.find(lower_heading)
        if pos != -1:
            heading_positions.append((pos, heading))

    # Sort by position
    heading_positions.sort(key=lambda x: x[0])

    # Calculate word counts between headings
    results: list[SectionHeading] = []
    for i, (pos, heading) in enumerate(heading_positions):
        # Start after the heading itself
        start = pos + len(heading)
        # End at next heading or end of text
        if i + 1 < len(heading_positions):
            end = heading_positions[i + 1][0]
        else:
            end = len(jd_text)

        section_text = jd_text[start:end]
        word_count = len(section_text.split())
        results.append(SectionHeading(name=heading, word_count=word_count))

    return results


def _validate_completeness(
    jd_text: str, llm_is_complete: bool, llm_confidence: float
) -> tuple[bool, float]:
    """
    Validate JD completeness using heuristics beyond LLM assessment.

    Args:
        jd_text: Extracted JD text
        llm_is_complete: LLM's assessment of completeness
        llm_confidence: LLM's confidence score (0.0-1.0)

    Returns:
        Tuple of (is_complete, final_confidence)
    """
    words = len(jd_text.split())

    # Check for truncation markers
    truncation_patterns = [
        "...",
        "read more",
        "sign in",
        "log in",
        "create account",
        "view full",
        "see more",
        "click here",
        "apply now",
        "[...]",
    ]
    text_lower = jd_text.lower()
    has_truncation = any(pattern in text_lower for pattern in truncation_patterns)

    # Minimum viable JD is ~300 words
    if words < 300:
        return False, min(llm_confidence, 0.6)

    # Truncation markers indicate incomplete content
    if has_truncation:
        return False, min(llm_confidence, 0.7)

    # Confidence threshold: only mark complete if LLM is confident
    if llm_confidence < 0.75:
        return False, llm_confidence

    # All checks passed
    return llm_is_complete, llm_confidence


def _format_error_message(e: Exception) -> str:
    """
    Format exception into user-friendly error message.

    Args:
        e: Exception from fetch/extract process

    Returns:
        User-friendly error message
    """
    error_str = str(e).lower()

    if "403" in error_str or "blocked" in error_str or "bot" in error_str:
        return "Site blocked automated access. Please paste the job description manually."
    elif "404" in error_str or "not found" in error_str:
        return "Job posting not found (404). The URL may be expired or incorrect."
    elif "timeout" in error_str or "timed out" in error_str:
        return "Request timed out. The site may be slow or unavailable. Try again or paste manually."
    elif "login" in error_str or "sign in" in error_str or "authentication" in error_str:
        return "This site requires login to view the full job description. Please paste it manually."
    elif "playwright" in error_str:
        return "This site requires JavaScript rendering. Please paste the job description manually."
    else:
        return f"Failed to fetch job description. Please paste it manually. (Error: {str(e)[:100]})"


@dataclass
class AnalyzeResult:
    """Result of analyzing user-provided JD text."""

    word_count: int
    section_headings: list[SectionHeading]


async def analyze_jd_text(jd_text: str) -> AnalyzeResult:
    """
    Analyze user-provided JD text to extract section headings.

    Used in edit mode to re-analyze text after user edits.

    Args:
        jd_text: The JD text to analyze

    Returns:
        AnalyzeResult with word_count and section_headings
    """
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_prompt = """Analyze the provided job description text and identify section headings.

Return a JSON object matching this schema:
{
  "section_headings": ["string array - exact heading text as it appears in the JD"]
}

Rules:
- Return the EXACT text of each section heading as it appears in the JD
- Common headings: "About Us", "Responsibilities", "Requirements", "Qualifications", "Benefits", "What You'll Do", etc.
- Only include actual headings/titles, not paragraph text or bullet points
- Return them in the order they appear in the document
- If no clear headings are found, return an empty array"""

    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Analyze this job description:\n\n{jd_text[:50000]}"}],
    )

    # Extract JSON from response
    text_content = "".join(
        block.text for block in response.content if block.type == "text"
    )

    import json

    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if not json_match:
        # Return empty result if no JSON found
        return AnalyzeResult(
            word_count=len(jd_text.split()),
            section_headings=[],
        )

    result = json.loads(json_match.group(0))
    headings = result.get("section_headings", [])

    # Calculate section word counts
    section_headings = _calculate_section_word_counts(jd_text, headings)

    return AnalyzeResult(
        word_count=len(jd_text.split()),
        section_headings=section_headings,
    )
