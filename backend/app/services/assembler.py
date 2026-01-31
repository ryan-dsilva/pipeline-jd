"""Assembler — combines selected cover letter options into a final draft.

This is a lightweight utility for when the user selects specific options
from each CL section and wants them stitched into a single document.
The cl_assembled section function handles the AI-powered assembly;
this module provides a simpler deterministic concatenation.
"""
from __future__ import annotations

from app.database import pb, record_to_dict


def get_assembled_draft(job_id: str) -> str | None:
    """Return the cl_assembled section content if it exists."""
    try:
        record = pb.collection("sections").get_first_list_item(
            f'job = "{job_id}" && section_key = "cl_assembled" && status = "complete"'
        )
        d = record_to_dict(record)
        return d.get("content_md")
    except Exception:
        return None


def get_all_cl_sections(job_id: str) -> dict[str, str]:
    """Return all completed cover letter sections as {key: content_md}."""
    records = pb.collection("sections").get_full_list(
        query_params={
            "filter": f'job = "{job_id}" && phase = "cover_letter" && status = "complete"',
        }
    )
    return {
        record_to_dict(r)["section_key"]: record_to_dict(r)["content_md"]
        for r in records
        if record_to_dict(r).get("content_md")
    }
