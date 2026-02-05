"""DAG-based pipeline executor.

Runs section functions respecting their dependency graph. Sections whose
dependencies are all satisfied run concurrently via asyncio. Progress is
reported through an async callback so the router can stream SSE events.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import AsyncIterator, Callable, Optional

from app.database import pb, record_to_dict, sanitize_pb_value, upsert_section
from app.models import JobResponse, PipelineEvent
from app.sections.config import (
    ANALYSIS_SECTIONS,
    COVER_LETTER_SECTIONS,
    SectionDef,
)
from app.sections.registry import SECTION_FUNCTIONS
from app.services.reference_loader import load_references

logger = logging.getLogger(__name__)


async def run_pipeline(
    job: JobResponse,
    phase: str,  # "analysis" | "cover_letter"
) -> AsyncIterator[PipelineEvent]:
    """Execute all sections for a phase, yielding SSE events as they complete."""

    section_defs = ANALYSIS_SECTIONS if phase == "analysis" else COVER_LETTER_SECTIONS

    # Pre-load all reference files (cached, so cheap after first call)
    refs = load_references(
        "li_profile", "resume", "mnookin_rubric", "role_analysis_template",
        "deep_analysis_reference", "quality_checklist", "hours_drivers",
        "research_checklist", "hm_research_checklist", "strategy_checklist",
        "glassdoor_method", "cover_letter_template", "approach", "cl_best_practices",
    )

    # Load any already-completed sections (for cover_letter phase, includes analysis)
    completed: dict[str, str] = {}
    if phase == "cover_letter":
        completed = _load_completed_sections(job.id)

    # Track which sections are locked (skip generation)
    locked_keys = _get_locked_keys(job.id)

    # Build pending set (skip locked sections that already have content)
    pending_defs = []
    for sd in section_defs:
        if sd.key in locked_keys and sd.key in completed:
            # Already done and locked — emit as complete immediately
            yield PipelineEvent(section_key=sd.key, status="complete")
        else:
            pending_defs.append(sd)

    # DAG execution: keep running until all pending sections are done
    in_flight: dict[str, asyncio.Task] = {}
    done_keys: set[str] = set(completed.keys())
    failed_keys: set[str] = set()

    while pending_defs or in_flight:
        # Find sections whose deps are all satisfied and not yet launched
        ready = [
            sd for sd in pending_defs
            if all(dep in done_keys for dep in sd.depends_on)
        ]

        for sd in ready:
            pending_defs.remove(sd)
            # Mark running in DB
            _update_section_status(job.id, sd, "running")
            yield PipelineEvent(section_key=sd.key, status="running")

            task = asyncio.create_task(
                _run_section(sd, job, refs, completed)
            )
            in_flight[sd.key] = task

        if not in_flight:
            # Nothing in flight and nothing ready — shouldn't happen unless
            # deps reference a failed section. Break to avoid infinite loop.
            break

        # Wait for at least one task to finish
        done_tasks, _ = await asyncio.wait(
            in_flight.values(),
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in done_tasks:
            # Find which key this task belongs to
            key = next(k for k, t in in_flight.items() if t is task)
            del in_flight[key]

            sd = next(s for s in section_defs if s.key == key)

            try:
                result = task.result()
                completed[key] = result.content_md
                done_keys.add(key)

                # Persist to DB
                _save_section_result(job.id, sd, result)

                # Special: evidence_cleanup also populates jobs.jd_cleaned
                if key == "evidence_cleanup":
                    _set_jd_cleaned(job.id, result.content_md)

                # Special: hours_estimate populates jobs.hours
                if key == "hours_estimate":
                    _extract_hours(job.id, result.content_md)

                yield PipelineEvent(
                    section_key=key,
                    status="complete",
                    content_md=result.content_md,
                )

            except Exception as exc:
                logger.exception("Section %s failed", key)
                failed_keys.add(key)
                done_keys.add(key)  # treat as done so dependents can detect
                _update_section_status(job.id, sd, "failed", str(exc))
                yield PipelineEvent(
                    section_key=key,
                    status="failed",
                    error_message=str(exc),
                )

    # After all sections complete, extract score/hours/verdict from final_verdict
    if phase == "analysis" and "final_verdict" in completed:
        _extract_verdict_metadata(job.id, completed["final_verdict"])

    # Update pipeline stage
    if phase == "analysis":
        _set_pipeline_stage(job.id, "analyzed")
    elif phase == "cover_letter":
        _set_pipeline_stage(job.id, "ready")


async def run_single_section(
    job: JobResponse,
    section_key: str,
) -> PipelineEvent:
    """Regenerate a single section (used by the sections router)."""
    from app.sections.config import ALL_SECTIONS

    sd = next((s for s in ALL_SECTIONS if s.key == section_key), None)
    if sd is None:
        return PipelineEvent(
            section_key=section_key,
            status="failed",
            error_message=f"Unknown section key: {section_key}",
        )

    refs = load_references(
        "li_profile", "resume", "mnookin_rubric", "role_analysis_template",
        "deep_analysis_reference", "quality_checklist", "hours_drivers",
        "research_checklist", "hm_research_checklist", "strategy_checklist",
        "glassdoor_method", "cover_letter_template", "approach", "cl_best_practices",
    )

    completed = _load_completed_sections(job.id)

    _update_section_status(job.id, sd, "running")

    try:
        result = await _run_section(sd, job, refs, completed)
        _save_section_result(job.id, sd, result)

        if section_key == "evidence_cleanup":
            _set_jd_cleaned(job.id, result.content_md)

        if section_key == "hours_estimate":
            _extract_hours(job.id, result.content_md)

        return PipelineEvent(
            section_key=section_key,
            status="complete",
            content_md=result.content_md,
        )
    except Exception as exc:
        logger.exception("Section %s failed", section_key)
        _update_section_status(job.id, sd, "failed", str(exc))
        return PipelineEvent(
            section_key=section_key,
            status="failed",
            error_message=str(exc),
        )


# ── Internal helpers ─────────────────────────────────────────────

async def _run_section(
    sd: SectionDef,
    job: JobResponse,
    refs: dict[str, str],
    completed: dict[str, str],
) -> "GenerationResult":
    """Run a section function in a thread (they are synchronous)."""
    from app.services.llm_service import GenerationResult

    dep_context = {
        dep_key: completed[dep_key]
        for dep_key in sd.depends_on
        if dep_key in completed
    }

    # For cover letter phase, pass all analysis sections as context too
    if sd.phase == "cover_letter":
        for k, v in completed.items():
            if k not in dep_context:
                dep_context[k] = v

    fn = SECTION_FUNCTIONS[sd.key]
    # Section functions are synchronous (they call the Anthropic SDK which is sync),
    # so run in a thread to avoid blocking the event loop.
    result = await asyncio.to_thread(fn, job, refs, dep_context)
    return result


def _load_completed_sections(job_id: str) -> dict[str, str]:
    """Load all completed sections for a job from the DB."""
    safe_id = sanitize_pb_value(job_id)
    records = pb.collection("sections").get_full_list(
        query_params={
            "filter": f"job = '{safe_id}' && status = 'complete'",
        }
    )
    result = {}
    for r in records:
        d = record_to_dict(r)
        if d.get("content_md"):
            result[d["section_key"]] = d["content_md"]
    return result


def _get_locked_keys(job_id: str) -> set[str]:
    """Get section keys that are locked."""
    safe_id = sanitize_pb_value(job_id)
    records = pb.collection("sections").get_full_list(
        query_params={
            "filter": f"job = '{safe_id}' && is_locked = true",
        }
    )
    return {record_to_dict(r)["section_key"] for r in records}


def _update_section_status(
    job_id: str,
    sd: SectionDef,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """Upsert a section row with the given status."""
    data = {
        "phase": sd.phase,
        "status": status,
        "is_locked": False,
    }
    if error_message:
        data["error_message"] = error_message

    upsert_section(job_id, sd.key, data)


def _save_section_result(job_id: str, sd: SectionDef, result) -> None:
    """Save a completed section result to the DB."""
    upsert_section(job_id, sd.key, {
        "phase": sd.phase,
        "status": "complete",
        "content_md": result.content_md,
        "model": result.model,
        "tokens_used": result.tokens_used,
        "generation_time_ms": result.generation_time_ms,
        "error_message": "",
        "is_locked": False,
    })


def _set_jd_cleaned(job_id: str, content: str) -> None:
    """Set the jd_cleaned field on the job (from evidence_cleanup output)."""
    pb.collection("jobs").update(job_id, {"jd_cleaned": content})


def _set_pipeline_stage(job_id: str, stage: str) -> None:
    """Update the pipeline_stage on the job."""
    pb.collection("jobs").update(job_id, {"pipeline_stage": stage})


def _extract_hours(job_id: str, hours_content: str) -> None:
    """Use Claude to extract a single average weekly-hours number from hours_estimate."""
    from pydantic import BaseModel
    from app.services.llm_service import call_llm

    class HoursResult(BaseModel):
        hours: int

    try:
        result = call_llm(
            system="Extract the hours as a single integer.", # Fixing prompt context too as it looked broken/missing in read?
            user=hours_content,
            use_web_search=False,
        )
        text = result.content_md
        json_str = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if json_str:
            result_obj = HoursResult.model_validate_json(json_str.group(0))
            pb.collection("jobs").update(job_id, {"hours": result_obj.hours})
    except Exception:
        logger.warning("Failed to extract hours for job %s", job_id, exc_info=True)


def _extract_verdict_metadata(job_id: str, verdict_content: str) -> None:
    """Parse score, hours, and verdict from final_verdict content and update job."""
    update: dict = {}

    # Try to extract score (e.g., "Total Score: 72/100" or "**Total Score:** 72/100")
    score_match = re.search(r"Total Score[:\s*]*(\d+)\s*/\s*100", verdict_content)
    if score_match:
        update["score"] = int(score_match.group(1))

    # Try to extract verdict
    for v in ["STRONG PURSUE", "HARD PASS", "PURSUE", "PASS"]:
        if v in verdict_content.upper():
            update["verdict"] = v
            break

    if update:
        pb.collection("jobs").update(job_id, update)
