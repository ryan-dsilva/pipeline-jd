"""Pipeline router — trigger analysis/cover-letter runs + SSE status stream."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import pb, record_to_dict, sanitize_pb_value
from app.models import JobResponse
from app.services.pipeline_executor import run_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


def _get_job_or_404(job_id: str) -> JobResponse:
    try:
        record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**record_to_dict(record))


# ── POST /api/pipeline/{job_id}/analyze ──────────────────────────

@router.post("/{job_id}/analyze")
async def start_analysis(job_id: str):
    job = _get_job_or_404(job_id)

    # Set stage to analyzing
    pb.collection("jobs").update(job_id, {"pipeline_stage": "analyzing"})

    async def event_stream():
        async for event in run_pipeline(job, "analysis"):
            data = event.model_dump_json()
            yield f"data: {data}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /api/pipeline/{job_id}/cover-letter ─────────────────────

@router.post("/{job_id}/cover-letter")
async def start_cover_letter(job_id: str):
    job = _get_job_or_404(job_id)

    # Set stage to cover_letter_gen
    pb.collection("jobs").update(job_id, {"pipeline_stage": "cover_letter_gen"})

    async def event_stream():
        async for event in run_pipeline(job, "cover_letter"):
            data = event.model_dump_json()
            yield f"data: {data}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /api/pipeline/{job_id}/status ────────────────────────────

@router.get("/{job_id}/status")
async def pipeline_status(job_id: str):
    """SSE stream that polls section statuses until pipeline is idle."""
    _get_job_or_404(job_id)  # 404 check

    async def status_stream():
        while True:
            sections = pb.collection("sections").get_full_list(
                query_params={
                    "filter": f"job = '{sanitize_pb_value(job_id)}'",
                    "fields": "section_key,status",
                }
            )
            statuses = {
                record_to_dict(r)["section_key"]: record_to_dict(r)["status"]
                for r in sections
            }
            yield f"data: {json.dumps(statuses)}\n\n"

            # If nothing is running, stop streaming
            if not any(s == "running" for s in statuses.values()):
                yield "data: {\"done\": true}\n\n"
                break

            await asyncio.sleep(2)

    return StreamingResponse(
        status_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
