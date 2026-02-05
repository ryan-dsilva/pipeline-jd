"""Analysis section generation functions (12 sections).

Each function has the signature:
    def generate_xxx(job, refs, dep_context) -> GenerationResult

- job: JobResponse (has .company, .role, .jd_text, .jd_cleaned)
- refs: dict[str, str] from reference_loader
- dep_context: dict[str, str] of completed dependency section content
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.llm_service import GenerationResult, call_llm
from app.services.reference_loader import load_references

if TYPE_CHECKING:
    from app.models import JobResponse


# ── 1. Evidence Cleanup ──────────────────────────────────────────

def generate_evidence_cleanup(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a JD evidence extractor. Clean up the raw job description into "
        "well-structured markdown. Preserve all details, and verbiage but organize into clear sections: "
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
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.1)


# ── 2. Gate Check ────────────────────────────────────────────────

def generate_gate_check(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a protective Executive Recruiter. Screen this role in 10 seconds. "
        "Output ONLY the bullet points and verdict. Absolutely NO preamble, NO summary, and NO post-text."
    )
    jd = dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Gate check this role: {job.company} — {job.role}

Cleaned JD:
{jd}

Instructions:
- Output exactly 4 lines of bullet points, then the verdict.
- Format: - **[Gate]:** [STATUS] | "Short Quote" (<15 words)
- Location: Strict SF or Remote. Reject South Bay/Peninsula (e.g. Palo Alto, San Jose).
- Level: Senior/Principal/Staff/Group/Lead.
- Red Flags: Burnout/chaos signals.
- Domain: B2B SaaS, AI/ML, Healthtech, Fintech, or adjacent.

**Final Verdict:** [PROCEED / STOP]
"""
    return call_llm(system=system, user=user, max_tokens=1000, temperature=0.0)


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
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


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
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


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
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


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
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.3, use_web_search=True)


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
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.2)


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
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.2)


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
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.2)


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
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.3)


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
    return call_llm(system=system, user=user, max_tokens=2000, temperature=0.2)


# ── 12. Final Verdict ────────────────────────────────────────────

def generate_final_verdict(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile")
    system = (
        "You are a strategic talent agent closing the deal. You don't just summarize; "
        "you connect the dots between the company's hidden struggle and the candidate's "
        "specific history. Your output is punchy, narrative, and high-signal."
    )
    user = f"""Synthesize the final verdict for {job.company} — {job.role}

Inputs:
- Health Score: {dep_context.get('scorecard_health', '0/40')}
- Role Fit Score: {dep_context.get('scorecard_role_fit', '0/30')}
- Personal Score: {dep_context.get('scorecard_personal', '0/30')}
- Deep Analysis: {dep_context.get('between_the_lines', 'N/A')}
- Hours/Risk: {dep_context.get('hours_estimate', 'N/A')}
- Candidate Profile: {r['li_profile']}

Instructions:
1. Sum the scores for the Total Score.
2. For "The Unicorn Match", map specific candidate achievements (from Profile) to specific role needs.

Output Format:

**Total Score:** [Sum]/100

**Between the lines:**
[One sharp paragraph: What is the company ACTUALLY trying to achieve? Use the deep analysis to find the "story behind the JD". e.g. "Google is trying to turn Gemini into a Fractional COO..."]

**The Unicorn Match:**
[Identify 3 specific "locks" where the candidate's past specifically solves the company's future]
- **[Theme 1]:** [Candidate's Specific Achievement] + [Role's Specific Need]. [Why it fits].
- **[Theme 2]:** ...
- **[Theme 3]:** ...

**Caution:**
[Blunt assessment of pace, hours, and burnout risk. e.g. "Expect wartime mode..."]

**Decision:** [STRONG PURSUE / PURSUE / PASS / HARD PASS]
"""
    return call_llm(system=system, user=user, max_tokens=1000, temperature=0.2)
