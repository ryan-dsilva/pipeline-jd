from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

REFERENCES_DIR = Path(__file__).resolve().parents[3] / "references"

# Map short keys used in section functions → filenames
_FILE_MAP = {
    "li_profile": "LI-Profile.md",
    "resume": "RyanDsilvaResume2025.md",
    "mnookin_rubric": "mnookin-rubric.md",
    "role_analysis_template": "role-analysis-template.md",
    "deep_analysis_reference": "deep-analysis-reference.md",
    "quality_checklist": "quality-checklist.md",
    "hours_drivers": "hours-per-week-drivers.md",
    "research_checklist": "research-checklist.md",
    "hm_research_checklist": "hm-research-checklist.md",
    "strategy_checklist": "strategy-checklist.md",
    "glassdoor_method": "glassdoor-method.md",
    "cover_letter_template": "cover-letter-template.md",
    "approach": "approach.md",
    "cl_best_practices": "cover-letter-best-practice-research.md",
}


@lru_cache(maxsize=None)
def load_reference(key: str) -> str:
    """Load a reference file by short key. Cached after first read."""
    filename = _FILE_MAP.get(key)
    if filename is None:
        raise KeyError(f"Unknown reference key: {key!r}. Valid keys: {sorted(_FILE_MAP)}")
    path = REFERENCES_DIR / filename
    return path.read_text(encoding="utf-8")


def load_references(*keys: str) -> dict[str, str]:
    """Load multiple reference files, returning {key: content}."""
    return {k: load_reference(k) for k in keys}
