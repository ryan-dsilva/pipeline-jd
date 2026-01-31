"""Analysis section generation functions (12 sections).

Each function has the signature:
    def generate_xxx(job, refs, dep_context) -> GenerationResult

- job: JobResponse (has .company, .role, .jd_text, .jd_cleaned)
- refs: dict[str, str] from reference_loader
- dep_context: dict[str, str] of completed dependency section content
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.claude_service import GenerationResult, call_claude
from app.services.reference_loader import load_references

if TYPE_CHECKING:
    from app.models import JobResponse


# ── 1. Evidence Cleanup ──────────────────────────────────────────

def generate_evidence_cleanup(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a JD evidence extractor. Clean up the raw job description into "
        "well-structured markdown. Preserve all details but organize into clear sections: "
        "Role Overview, Responsibilities, Requirements, Nice-to-Haves, Benefits, and any "
        "other relevant sections. Extract and highlight 10-12 key quotes that reveal the "
        "most about the role's true nature, expectations, and culture signals."
    )
    user = f"""Clean and structure this job description for {job.company} — {job.role}.

Raw JD Text:
{job.jd_text}

Instructions:
1. Reformat into clean markdown with clear section headers.
2. Preserve ALL content — do not summarize or remove details.
3. At the end, add a "## Key Quotes" section with 10-12 quotes extracted verbatim
   from the JD that are most revealing about the role, expectations, and culture.
4. For each quote, add a brief inline note about what it signals.
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.1)


# ── 2. Gate Check ────────────────────────────────────────────────

def generate_gate_check(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a role-fit gate checker for a 49yo Senior Principal PM who prioritizes "
        "health-first, sustainable pace, and avoids chaotic leadership. Your job is to "
        "quickly assess whether this role passes basic filters before investing in deep research."
    )
    jd = dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Gate check this role: {job.company} — {job.role}

Cleaned JD:
{jd}

Check these gates:
1. **Location:** Must be Remote or Hybrid (SF Bay Area). If not, flag as HARD PASS.
2. **Level:** Must be Senior/Principal/Staff PM level. If junior, flag.
3. **Red flags:** Excessive travel, on-call, "fast-paced startup" without structure signals.
4. **Domain fit:** Does this align with B2B SaaS, AI/ML, Healthtech, or Fintech?

Output format:
- PASS / CAUTION / HARD PASS for each gate
- Brief rationale per gate
- Overall recommendation: PROCEED / PAUSE / STOP
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.1)


# ── 3. Company Research ──────────────────────────────────────────

def generate_company_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("research_checklist", "li_profile")
    system = (
        "You are a senior company researcher. Your task is to research a company to help "
        "evaluate role fit for a growth-minded Senior Principal PM who avoids chaotic "
        "leadership and hero-mode expectations.\n\n"
        "Quality gates:\n"
        "- Source diversity: at least 5 sources across 4 distinct domains\n"
        "- Leadership detail: founders and execs with prior roles, tenure, achievements\n"
        "- Culture/WLB stance: at least one explicit public stance with citation\n"
        "- Founder content: posts, videos, or announcements per founder if available\n"
        "- Citations required for each section; use inline markdown links [domain](url)"
    )
    jd = job.jd_cleaned or dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Research {job.company} for the role: {job.role}

Cleaned Job Description:
{jd}

Gate Check Results:
{dep_context.get('gate_check', 'N/A')}

Research Checklist:
{r['research_checklist']}

LinkedIn Profile (candidate context):
{r['li_profile']}
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


# ── 4. Leadership Research ───────────────────────────────────────

def generate_leadership_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("hm_research_checklist")
    system = (
        "You are a hiring manager researcher. Find the most likely hiring manager for this "
        "role and summarize their management style, focusing on leadership maturity, boundary "
        "signals, and sustainable-pace fit.\n\n"
        "Quality gates:\n"
        "- Identify likely hiring manager or head of product with confidence level\n"
        "- Include prior roles and tenure lengths\n"
        "- Provide at least one leadership/culture signal with citation\n"
        "- Use at least 2 sources (LinkedIn + interview/podcast/company blog)\n"
        "- Citations required; use inline markdown links [domain](url)"
    )
    jd = job.jd_cleaned or dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Research the hiring manager for {job.company} — {job.role}

Cleaned Job Description:
{jd}

Gate Check Results:
{dep_context.get('gate_check', 'N/A')}

HM Research Checklist:
{r['hm_research_checklist']}
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


# ── 5. Strategy Research ─────────────────────────────────────────

def generate_strategy_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("strategy_checklist")
    system = (
        "You are a product strategy researcher. Summarize product strategy and market "
        "positioning for this company, emphasizing whether the strategy fits a Senior "
        "Principal PM's strengths (Applied AI, B2B, scaling) and implies sustainable pace.\n\n"
        "Quality gates:\n"
        "- Source diversity: at least 4 sources across 3 distinct domains\n"
        "- Competitor list: 3-5 direct or adjacent competitors with citations\n"
        "- Differentiators: 2-3 specific differentiators with citations\n"
        "- Pricing: capture pricing structure, levels, and implications\n"
        "- Recency: at least one source from the last 12 months\n"
        "- Citations required; use inline markdown links [domain](url)"
    )
    jd = job.jd_cleaned or dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Research product strategy for {job.company} — {job.role}

Cleaned Job Description:
{jd}

Gate Check Results:
{dep_context.get('gate_check', 'N/A')}

Strategy Checklist:
{r['strategy_checklist']}
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


# ── 6. Glassdoor Research ────────────────────────────────────────

def generate_glassdoor_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("glassdoor_method")
    system = (
        "You are a WLB/Glassdoor researcher. Provide a concise summary of work-life "
        "balance signals for this company, emphasizing sustainability risks for a "
        "health-first Senior Principal PM.\n\n"
        "Quality gates:\n"
        "- Provide WLB rating if available; otherwise mark unavailable\n"
        "- Summarize at least 2 contrasting themes (positive + negative) with citations\n"
        "- Use at least 2 sources if Glassdoor is gated (Indeed, Comparably, Blind)\n"
        "- Citations required; use inline markdown links [domain](url)"
    )
    user = f"""Research work-life balance and employee reviews for {job.company}

Role context: {job.role}

Glassdoor Method:
{r['glassdoor_method']}
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.3, use_web_search=True)


# ── 7. Scorecard: Health & Maturity (40pts) ──────────────────────

def generate_scorecard_health(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = (
        "You are a role-fit scoring expert using the Mnookin rubric. Score the Health & "
        "Maturity dimension (40 points total) for a 49yo Senior Principal PM who prioritizes "
        "health-first, sustainable pace."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Score Health & Maturity (40pts) for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}

Mnookin Rubric:
{r['mnookin_rubric']}

Deep Analysis Reference:
{r['deep_analysis_reference']}

Score these sub-dimensions with points and rationale:
- Company Maturity & Stability
- Leadership Quality & Maturity
- Work-Life Balance & Sustainability
- Culture & Values Alignment

Format: bullet per sub-dimension with score, rationale, and key evidence.
Total at the end: X/40
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.2)


# ── 8. Scorecard: Role Fit (30pts) ───────────────────────────────

def generate_scorecard_role_fit(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = (
        "You are a role-fit scoring expert using the Mnookin rubric. Score the Role Fit "
        "dimension (30 points total) for a 49yo Senior Principal PM."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Score Role Fit (30pts) for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Leadership Research:
{dep_context.get('leadership_research', 'N/A')}

Strategy Research:
{dep_context.get('strategy_research', 'N/A')}

Mnookin Rubric:
{r['mnookin_rubric']}

Deep Analysis Reference:
{r['deep_analysis_reference']}

Score these sub-dimensions with points and rationale:
- Skill Match & Technical Alignment
- Level & Scope Fit
- Domain Relevance
- Growth & Learning Potential

Format: bullet per sub-dimension with score, rationale, and key evidence.
Total at the end: X/30
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.2)


# ── 9. Scorecard: Personal + Bonus (30pts) ───────────────────────

def generate_scorecard_personal(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = (
        "You are a role-fit scoring expert using the Mnookin rubric. Score the Personal "
        "& Bonus dimension (30 points total) for a 49yo Senior Principal PM."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Score Personal + Bonus (30pts) for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}

Mnookin Rubric:
{r['mnookin_rubric']}

Deep Analysis Reference:
{r['deep_analysis_reference']}

Score these sub-dimensions with points and rationale:
- Mission & Personal Motivation
- Compensation & Benefits Signals
- Location & Flexibility
- Bonus Factors (unique opportunities, network, brand)

Format: bullet per sub-dimension with score, rationale, and key evidence.
Total at the end: X/30
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.2)


# ── 10. Between the Lines ────────────────────────────────────────

def generate_between_the_lines(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a senior career coach who reads between the lines of job descriptions. "
        "Apply a deep analytical lens to surface what the JD is really saying about the "
        "role, the team, and the hiring manager's true needs."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Read between the lines for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Leadership Research:
{dep_context.get('leadership_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}

Analyze:
1. **Archetype:** Is this a Craftsperson, Operator, or Visionary role? Evidence?
2. **Personality:** What specific traits are they ACTUALLY hiring for?
3. **Operating Style:** Scrappy vs Process, Data vs Intuition — cite evidence.
4. **Hidden Risks:** Politics, pace, leadership maturity concerns.
5. **Political Context:** Tie to org events (funding, leadership changes, pivots).
6. **What's NOT said:** What's conspicuously absent from the JD?

Use 2-3 longer-form JD quotes (1-2 sentences) to anchor each point.
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.3)


# ── 11. Hours Estimate ───────────────────────────────────────────

def generate_hours_estimate(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("hours_drivers")
    system = (
        "You are an expert at estimating weekly work hours for tech roles. Triangulate "
        "from multiple signals to provide a specific hours estimate (e.g., '50-55h'), "
        "not a vague range."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Estimate weekly hours for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Leadership Research:
{dep_context.get('leadership_research', 'N/A')}

Hours Drivers Framework:
{r['hours_drivers']}

Triangulate from:
1. Sprint language and delivery cadence signals in JD
2. Founder/leadership background and expectations
3. Glassdoor/review WLB signals
4. Company stage and funding pressure
5. Role scope and cross-functional demands

Output:
- **Estimate:** X-Yh/week
- **Confidence:** High/Medium/Low
- Evidence for each signal source
- Key risks that could push hours higher
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.2)


# ── 12. Final Verdict ────────────────────────────────────────────

def generate_final_verdict(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("role_analysis_template", "quality_checklist")
    system = (
        "You are a career coach providing a final verdict on role fit for a 49yo Senior "
        "Principal PM who prioritizes health-first, sustainable pace. Be candid, direct, "
        "and protective of time/energy. Use the Coach persona."
    )
    user = f"""Provide a final verdict for {job.company} — {job.role}

Health & Maturity Scorecard:
{dep_context.get('scorecard_health', 'N/A')}

Role Fit Scorecard:
{dep_context.get('scorecard_role_fit', 'N/A')}

Personal Scorecard:
{dep_context.get('scorecard_personal', 'N/A')}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

Hours Estimate:
{dep_context.get('hours_estimate', 'N/A')}

Quality Checklist:
{r['quality_checklist']}

Role Analysis Template (for output format):
{r['role_analysis_template']}

Provide:
1. **Total Score:** X/100 (sum of three scorecards)
2. **Expected Hours:** from hours estimate
3. **Decision:** STRONG PURSUE / PURSUE / PASS / HARD PASS
4. **Coach's Summary:** 2-3 paragraphs synthesizing "Is this worth it?" for this persona.
   Include 2-3 longer-form JD quotes to anchor your synthesis.
5. **Key Risks:** Top 3 risks with mitigation strategies
6. **Key Opportunities:** Top 3 reasons to pursue
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.2)
