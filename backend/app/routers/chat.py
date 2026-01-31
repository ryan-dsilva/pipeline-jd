"""Chat router — streaming chat with all sections as context."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import anthropic

from app.config import settings
from app.database import pb, record_to_dict, sanitize_pb_value
from app.models import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── POST /api/chat/{job_id} ──────────────────────────────────────

@router.post("/{job_id}")
async def chat(job_id: str, body: ChatRequest):
    """Chat with all completed sections as context. Streams the response via SSE."""
    # Load job
    try:
        job_record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    job = record_to_dict(job_record)

    # Load all completed sections as context
    sections = pb.collection("sections").get_full_list(
        query_params={
            "filter": f"job = '{sanitize_pb_value(job_id)}' && status = 'complete'",
            "sort": "created",
        }
    )

    # Build system prompt with all section content
    section_context = ""
    for s in sections:
        s_dict = record_to_dict(s)
        if s_dict.get("content_md"):
            section_context += f"\n\n## {s_dict['section_key']}\n{s_dict['content_md']}"

    jd_text = job.get("jd_cleaned") or job.get("jd_text") or ""

    system_prompt = f"""You are a career advisor assistant helping evaluate and prepare for the role of {job['role']} at {job['company']}.

You have access to the following analysis and cover letter sections that have been generated for this role. Use them to provide informed, specific answers.

## Job Description
{jd_text}

## Analysis & Cover Letter Sections
{section_context}

Guidelines:
- Be specific and reference the analysis when relevant.
- If asked about something not covered in the sections, say so and offer to help based on what you do know.
- Maintain a professional, direct tone. Be candid about risks and opportunities.
- When suggesting edits to cover letter sections, provide the full revised text."""

    # Build messages from history + new message
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in body.history
    ]
    messages.append({"role": "user", "content": body.message})

    async_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def stream_response():
        async with async_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                # SSE format: each chunk as a data event
                yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
