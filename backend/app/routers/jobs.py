"""Jobs router — CRUD operations for jobs."""

from __future__ import annotations

import asyncio
import re
import time
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.database import pb, record_to_dict, sanitize_pb_value
from app.extraction import extract_company_role
from app.models import (
    JobCreate,
    JobDetailResponse,
    JobFetchRequest,
    JobFetchResponse,
    JobResponse,
    JobStageUpdate,
    JobTextAnalyzeRequest,
    JobTextAnalyzeResponse,
    JobUpdate,
    PIPELINE_STAGES,
    SectionHeadingResponse,
    SectionResponse,
)
from app.services.jd_fetcher import analyze_jd_text, fetch_jd_from_url
from app.services.pipeline_executor import run_pipeline

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ── POST /api/jobs/fetch-jd ──────────────────────────────────────


@router.post("/fetch-jd", response_model=JobFetchResponse)
async def fetch_job_description(body: JobFetchRequest):
    """
    Fetch job description content from URL.
    Does not create a job — only fetches and extracts content.
    """
    # Validate URL format
    if not body.jd_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )

    # Check for duplicate URL
    try:
        existing = pb.collection("jobs").get_first_list_item(
            f"jd_url = '{sanitize_pb_value(body.jd_url)}'"
        )
        raise HTTPException(
            status_code=409,
            detail=f"Job with this URL already exists: {existing.id}",
        )
    except HTTPException:
        raise
    except Exception:
        pass  # Not found — good

    # Attempt fetch
    result = await fetch_jd_from_url(body.jd_url)

    return JobFetchResponse(
        success=result.success,
        jd_text=result.jd_text,
        is_complete=result.is_complete,
        confidence=result.confidence,
        word_count=result.word_count,
        html_word_count=result.html_word_count,
        section_headings=[
            SectionHeadingResponse(name=h.name, word_count=h.word_count)
            for h in result.section_headings
        ],
        method_used=result.method_used,
        error_message=result.error_message,
    )


# ── POST /api/jobs/analyze-text ───────────────────────────────────


@router.post("/analyze-text", response_model=JobTextAnalyzeResponse)
async def analyze_text(body: JobTextAnalyzeRequest):
    """
    Analyze JD text to extract section headings and word counts.
    Used in edit mode to re-analyze after user edits.
    """
    result = await analyze_jd_text(body.jd_text)

    return JobTextAnalyzeResponse(
        word_count=result.word_count,
        section_headings=[
            SectionHeadingResponse(name=h.name, word_count=h.word_count)
            for h in result.section_headings
        ],
    )


def _make_slug(company: str, role: str) -> str:
    """Generate a URL-friendly job ID: company-role-YYYYMMDD."""
    base = f"{company}-{role}-{date.today().isoformat()}"
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return slug


# ── POST /api/jobs ───────────────────────────────────────────────


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(body: JobCreate):
    # Check for duplicate URL
    try:
        existing = pb.collection("jobs").get_first_list_item(
            f"jd_url = '{sanitize_pb_value(body.jd_url)}'"
        )
        raise HTTPException(
            status_code=409,
            detail=f"Job with this URL already exists: {existing.id}",
        )
    except HTTPException:
        raise
    except Exception:
        pass  # Not found — good

    # Create temporary slug based on timestamp
    temp_slug = f"jd-{int(time.time())}"

    # Create job with empty company/role
    # extraction_status: pending if we have text, failed if no text (will need manual entry)
    row = {
        "slug": temp_slug,
        "company": "",
        "role": "",
        "jd_url": body.jd_url,
        "jd_text": body.jd_text,  # Can be None
        "jd_fetch_status": body.jd_fetch_status,
        "jd_fetch_confidence": body.jd_fetch_confidence,
        "date_added": date.today().isoformat(),
        "pipeline_stage": "queue",
        "extraction_status": "pending" if body.jd_text else "failed",
    }
    record = pb.collection("jobs").create(row)
    job_id = record.id

    # Run extraction inline only if we have jd_text
    if body.jd_text:
        try:
            extracted = await extract_company_role(body.jd_text)
            company = extracted.get("company", "Unknown")
            role = extracted.get("role", "Unknown")

            # Generate proper slug from extracted data
            slug = _make_slug(company, role)

            # Handle slug collision
            base_slug = slug
            counter = 2
            while True:
                try:
                    pb.collection("jobs").get_first_list_item(
                        f"slug = '{sanitize_pb_value(slug)}'"
                    )
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                except Exception:
                    break

            # Update job with extracted data
            record = pb.collection("jobs").update(
                job_id,
                {
                    "company": company,
                    "role": role,
                    "slug": slug,
                    "extraction_status": "complete",
                },
            )
        except Exception:
            # Extraction failed, mark as failed but keep the job
            pb.collection("jobs").update(job_id, {"extraction_status": "failed"})
            record = pb.collection("jobs").get_one(job_id)

    # Re-fetch to ensure all system fields (created/updated) and schema fields are populated.
    record = pb.collection("jobs").get_one(job_id)
    job_data = record_to_dict(record)

    # Auto-start analysis if extraction succeeded
    if job_data.get("extraction_status") == "complete" and body.jd_text:
        asyncio.create_task(_trigger_analysis_async(job_data))

    return job_data


async def _trigger_analysis_async(job_data: dict) -> None:
    """Trigger analysis pipeline in the background after job creation."""
    from app.models import JobResponse

    job = JobResponse(**job_data)
    # Run the pipeline - it will update the stage from queue -> analyzing -> analyzed
    async for _ in run_pipeline(job, "analysis"):
        pass  # Consume the async generator


# ── GET /api/jobs ────────────────────────────────────────────────


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    stage: str | None = Query(None),
    search: str | None = Query(None),
):
    filters = []
    if stage:
        filters.append(f"pipeline_stage = '{sanitize_pb_value(stage)}'")
    if search:
        filters.append(f"company ~ '{sanitize_pb_value(search)}'")

    filter_str = " && ".join(filters) if filters else ""
    query_params = {"sort": "-date_added"}
    if filter_str:
        query_params["filter"] = filter_str

    records = pb.collection("jobs").get_full_list(query_params=query_params)
    return [record_to_dict(r) for r in records]


# ── GET /api/jobs/{job_id} ───────────────────────────────────────


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str):
    try:
        record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    sections = pb.collection("sections").get_full_list(
        query_params={
            "filter": f"job = '{sanitize_pb_value(job_id)}'",
            "sort": "created",
        }
    )

    job = record_to_dict(record)
    job["sections"] = [record_to_dict(s) for s in sections]
    return job


# ── DELETE /api/jobs/{job_id} ────────────────────────────────────


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str):
    try:
        pb.collection("jobs").delete(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")


# ── PUT /api/jobs/{job_id}/stage ─────────────────────────────────


@router.put("/{job_id}/stage", response_model=JobResponse)
async def update_stage(job_id: str, body: JobStageUpdate):
    if body.stage not in PIPELINE_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}",
        )

    try:
        record = pb.collection("jobs").update(job_id, {"pipeline_stage": body.stage})
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return record_to_dict(record)


# ── POST /api/jobs/{job_id}/extract ──────────────────────────────


@router.post("/{job_id}/extract", response_model=JobResponse)
async def reextract_job(job_id: str):
    """Re-run extraction on an existing job."""
    try:
        record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = record_to_dict(record)
    jd_text = job_data.get("jd_text", "")

    if not jd_text:
        raise HTTPException(
            status_code=400, detail="Job has no JD text to extract from"
        )

    # Update status to running
    pb.collection("jobs").update(job_id, {"extraction_status": "running"})

    try:
        extracted = await extract_company_role(jd_text)
        company = extracted.get("company", "Unknown")
        role = extracted.get("role", "Unknown")

        # Generate new slug
        slug = _make_slug(company, role)

        # Handle slug collision
        base_slug = slug
        counter = 2
        while True:
            try:
                existing = pb.collection("jobs").get_first_list_item(
                    f"slug = '{sanitize_pb_value(slug)}'"
                )
                # If it's the same job, keep the slug
                if existing.id == job_id:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            except Exception:
                break

        # Update job with extracted data
        record = pb.collection("jobs").update(
            job_id,
            {
                "company": company,
                "role": role,
                "slug": slug,
                "extraction_status": "complete",
            },
        )
    except Exception as e:
        # Extraction failed
        pb.collection("jobs").update(job_id, {"extraction_status": "failed"})
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    return record_to_dict(record)


# ── PATCH /api/jobs/{job_id} ─────────────────────────────────────


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, body: JobUpdate):
    """Manually update company and/or role."""
    try:
        record = pb.collection("jobs").get_one(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = record_to_dict(record)
    updates = {}

    # Update company and/or role
    if body.company is not None:
        updates["company"] = body.company
    if body.role is not None:
        updates["role"] = body.role

    if not updates:
        # Nothing to update
        return job_data

    # Regenerate slug if company or role changed
    company = updates.get("company", job_data.get("company", ""))
    role = updates.get("role", job_data.get("role", ""))

    slug = _make_slug(company, role)

    # Handle slug collision
    base_slug = slug
    counter = 2
    while True:
        try:
            existing = pb.collection("jobs").get_first_list_item(
                f"slug = '{sanitize_pb_value(slug)}'"
            )
            if existing.id == job_id:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        except Exception:
            break

    updates["slug"] = slug

    try:
        record = pb.collection("jobs").update(job_id, updates)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update job")

    return record_to_dict(record)
