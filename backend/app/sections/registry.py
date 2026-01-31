"""Section function registry — maps section_key to generation function."""
from app.sections.analysis import (
    generate_between_the_lines,
    generate_company_research,
    generate_evidence_cleanup,
    generate_final_verdict,
    generate_gate_check,
    generate_glassdoor_research,
    generate_hours_estimate,
    generate_leadership_research,
    generate_scorecard_health,
    generate_scorecard_personal,
    generate_scorecard_role_fit,
    generate_strategy_research,
)
from app.sections.cover_letter import (
    generate_cl_assembled,
    generate_cl_closing,
    generate_cl_intro,
    generate_cl_pep_talk,
    generate_cl_problem,
    generate_cl_proof,
    generate_cl_resume_headlines,
    generate_cl_why_now,
)

SECTION_FUNCTIONS = {
    # Analysis (12)
    "evidence_cleanup": generate_evidence_cleanup,
    "gate_check": generate_gate_check,
    "company_research": generate_company_research,
    "leadership_research": generate_leadership_research,
    "strategy_research": generate_strategy_research,
    "glassdoor_research": generate_glassdoor_research,
    "scorecard_health": generate_scorecard_health,
    "scorecard_role_fit": generate_scorecard_role_fit,
    "scorecard_personal": generate_scorecard_personal,
    "between_the_lines": generate_between_the_lines,
    "hours_estimate": generate_hours_estimate,
    "final_verdict": generate_final_verdict,
    # Cover Letter (8)
    "cl_pep_talk": generate_cl_pep_talk,
    "cl_resume_headlines": generate_cl_resume_headlines,
    "cl_intro": generate_cl_intro,
    "cl_problem": generate_cl_problem,
    "cl_proof": generate_cl_proof,
    "cl_why_now": generate_cl_why_now,
    "cl_closing": generate_cl_closing,
    "cl_assembled": generate_cl_assembled,
}
