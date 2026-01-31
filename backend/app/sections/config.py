from dataclasses import dataclass
from typing import List


@dataclass
class SectionDef:
    key: str
    label: str
    order: int
    depends_on: List[str]
    phase: str


ANALYSIS_SECTIONS = [
    SectionDef("evidence_cleanup", "Evidence Cleanup", 20, [], "analysis"),
    SectionDef("gate_check", "Gate Check", 7, ["evidence_cleanup"], "analysis"),
    SectionDef("company_research", "Company Research", 8, ["gate_check"], "analysis"),
    SectionDef("leadership_research", "Leadership Research", 9, ["gate_check"], "analysis"),
    SectionDef("strategy_research", "Strategy Research", 10, ["gate_check"], "analysis"),
    SectionDef("glassdoor_research", "Glassdoor Research", 11, ["gate_check"], "analysis"),
    SectionDef("scorecard_health", "Health & Maturity (40pts)", 3, ["company_research", "glassdoor_research"], "analysis"),
    SectionDef("scorecard_role_fit", "Role Fit (30pts)", 4, ["company_research", "leadership_research", "strategy_research"], "analysis"),
    SectionDef("scorecard_personal", "Personal + Bonus (30pts)", 5, ["company_research", "glassdoor_research"], "analysis"),
    SectionDef("between_the_lines", "Between the Lines", 2, ["company_research", "leadership_research", "glassdoor_research"], "analysis"),
    SectionDef("hours_estimate", "Hours Estimate", 6, ["company_research", "leadership_research"], "analysis"),
    SectionDef("final_verdict", "Final Verdict", 1, ["scorecard_health", "scorecard_role_fit", "scorecard_personal", "between_the_lines", "hours_estimate"], "analysis"),
]

COVER_LETTER_SECTIONS = [
    SectionDef("cl_pep_talk", "Pep Talk", 12, [], "cover_letter"),
    SectionDef("cl_resume_headlines", "Resume Headlines", 13, [], "cover_letter"),
    SectionDef("cl_intro", "Introduction (3 options)", 14, [], "cover_letter"),
    SectionDef("cl_problem", "Problem Statement (2 options)", 15, [], "cover_letter"),
    SectionDef("cl_proof", "Proof Points (2 options)", 16, [], "cover_letter"),
    SectionDef("cl_why_now", "Why Now (2 options)", 17, [], "cover_letter"),
    SectionDef("cl_closing", "Closing (2 options)", 18, [], "cover_letter"),
    SectionDef("cl_assembled", "Assembled Drafts (2 options)", 19, ["cl_intro", "cl_problem", "cl_proof", "cl_why_now", "cl_closing"], "cover_letter"),
]

ALL_SECTIONS = ANALYSIS_SECTIONS + COVER_LETTER_SECTIONS
