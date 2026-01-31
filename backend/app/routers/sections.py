"""Sections router — read, edit, regenerate, lock individual sections."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import pb, record_to_dict, sanitize_pb_value
from app.models import (
    JobResponse,
    SectionDefinitionResponse,
    SectionLockToggle,
    SectionResponse,
    SectionUpdate,
)
from app.sections.config import ALL_SECTIONS
from app.services.pipeline_executor import run_single_section

router = APIRouter(prefix="/api/sections", tags=["sections"])

section_definitions_router = APIRouter(tags=["sections"])


def _get_job_or_404(job_id: str) -> JobResponse:
    try:
        record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**record_to_dict(record))


# ── GET /api/section-definitions ─────────────────────────────────

@section_definitions_router.get(
    "/api/section-definitions",
    response_model=list[SectionDefinitionResponse],
    tags=["sections"],
)
async def get_section_definitions():
    """Return all section definitions for frontend rendering."""
    return [
        SectionDefinitionResponse(
            key=sd.key,
            label=sd.label,
            order=sd.order,
            depends_on=sd.depends_on,
            phase=sd.phase,
        )
        for sd in ALL_SECTIONS
    ]


# ── GET /api/sections/{job_id} ───────────────────────────────────

@router.get("/{job_id}", response_model=list[SectionResponse])
async def list_sections(job_id: str):
    _get_job_or_404(job_id)
    records = pb.collection("sections").get_full_list(
        query_params={
            "filter": f"job = '{sanitize_pb_value(job_id)}'",
            "sort": "created",
        }
    )
    return [record_to_dict(r) for r in records]


# ── GET /api/sections/{job_id}/{key} ─────────────────────────────

@router.get("/{job_id}/{key}", response_model=SectionResponse)
async def get_section(job_id: str, key: str):
    try:
        record = pb.collection("sections").get_first_list_item(
            f"job = '{sanitize_pb_value(job_id)}' && section_key = '{sanitize_pb_value(key)}'"
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Section not found")
    return record_to_dict(record)


# ── PUT /api/sections/{job_id}/{key} ─────────────────────────────

@router.put("/{job_id}/{key}", response_model=SectionResponse)
async def update_section(job_id: str, key: str, body: SectionUpdate):
    """Edit section content. Auto-locks the section."""
    try:
        existing = pb.collection("sections").get_first_list_item(
            f"job = '{sanitize_pb_value(job_id)}' && section_key = '{sanitize_pb_value(key)}'"
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Section not found")

    record = pb.collection("sections").update(
        existing.id,
        {"content_md": body.content_md, "is_locked": True},
    )
    return record_to_dict(record)


# ── POST /api/sections/{job_id}/{key}/generate ───────────────────

@router.post("/{job_id}/{key}/generate", response_model=SectionResponse)
async def regenerate_section(job_id: str, key: str):
    """Regenerate a single section (unlocks it first)."""
    job = _get_job_or_404(job_id)

    # Unlock before regenerating
    try:
        existing = pb.collection("sections").get_first_list_item(
            f"job = '{sanitize_pb_value(job_id)}' && section_key = '{sanitize_pb_value(key)}'"
        )
        pb.collection("sections").update(existing.id, {"is_locked": False})
    except Exception:
        pass  # Section may not exist yet

    event = await run_single_section(job, key)

    if event.status == "failed":
        raise HTTPException(status_code=500, detail=event.error_message)

    # Return the updated section
    record = pb.collection("sections").get_first_list_item(
        f"job = '{sanitize_pb_value(job_id)}' && section_key = '{sanitize_pb_value(key)}'"
    )
    return record_to_dict(record)


# ── POST /api/sections/{job_id}/{key}/lock ───────────────────────

@router.post("/{job_id}/{key}/lock", response_model=SectionResponse)
async def toggle_lock(job_id: str, key: str, body: SectionLockToggle):
    try:
        existing = pb.collection("sections").get_first_list_item(
            f"job = '{sanitize_pb_value(job_id)}' && section_key = '{sanitize_pb_value(key)}'"
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Section not found")

    record = pb.collection("sections").update(
        existing.id, {"is_locked": body.is_locked}
    )
    return record_to_dict(record)
