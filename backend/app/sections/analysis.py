"""Analysis section generation functions (12 sections).

Each function has the signature:
    def generate_xxx(job, refs, dep_context) -> GenerationResult

- job: JobResponse (has .company, .role, .jd_text, .jd_cleaned)
- refs: dict[str, str] from reference_loader
- dep_context: dict[str, str] of completed dependency section content
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.llm_service import GenerationResult, call_llm, call_llm_with_cache
from app.services.reference_loader import load_references

if TYPE_CHECKING:
    from app.models import JobResponse

target_audience = """
## Target Audience 
- A 49-year-old Principal Product Manager seeking health-first, sustainable pace roles in (preferred) B2B SaaS, AI/ML, Healthtech, or Fintech.
"""
writing_style = """
## Style 
- Write in clear, concise, high-signal bullet points for an executive, technical product manager. 

## IMPORTANT Verification Rules
1. No headers, no preamble, no epilogue.
2. Prefer bullet points with bolded leaders. eg. **[1-3 word takeaway]:** Content.
3. Paragraphs when a narrative is needed.
4. Conduct external research as needed to ensure accuracy and completeness. Citations must included.
5. Citations must be inline markdown links [domain](full, untrimmed, accurate url). Place citations at the end of the sentence, BEFORE the period.
6. Remove all additional newlines and extraneous whitespace. Ensure punctuation immediately follows the word or link. NO isolated periods on new lines.
"""

# ── 1. Evidence Cleanup ──────────────────────────────────────────

def generate_evidence_cleanup(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = f"""
## Role
You are a job description evidence extractor.

{target_audience}

## Task
Extract and clean up the job description text to make it more readable and structured for analysis.

## Requirements
- Preserve ALL content — do not summarize or remove details.
- Clean up the raw job description into 
- well-structured markdown. Preserve all details, and verbiage but organize into clear sections: 
- Role Overview, Responsibilities, Requirements, Nice-to-Haves, Benefits, and any 
- other relevant sections. Extract and highlight 10-12 key quotes that reveal the 
- most about the role's true nature, expectations, and culture signals.
- At the start of the text, provide a "## Key Quotes" section with 10-12 quotes extracted verbatim from the JD
    - Pick quotes that are differentiated and most revealing about the role, expectations, and culture. 
    - For each quote, add a brief inline note about what it signals.
"""
    user = f"""
Extract and structure this job description for {job.company} — {job.role}.
Raw JD Text:
---
{job.jd_text}
"""
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.1)


# ── 2. Gate Check ────────────────────────────────────────────────

def generate_gate_check(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = f"""
## Role
You are a executive recruiter invested in my success.

## Tasks
Check if this role passes my strict gate criteria for Senior/Principal PM roles.

{target_audience}

## Requirements
- Output the verdict, then exactly 4 lines of bullet points explaining each gate.

## Format
**Final Verdict:** [PROCEED / STOP]
 (Format for the next 4 bullets: **[Gate]:** [STATUS] | Short explanation of <20 words)
- (✅ or ❌) Location: Strict SF or Remote. Reject South Bay/Peninsula (e.g. Palo Alto, San Jose).
- (✅ or ❌) Level: Senior/Principal/Staff/Group/Lead.
- (✅ or ❌) Red Flags: Burnout/chaos signals.
- (✅ or ❌)Domain: B2B SaaS, AI/ML, Healthtech, Fintech, or adjacent.
(No preamble, no epilogue)

{writing_style}
"""
    jd = dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""Check if this role is a proceed / stop: {job.company} — {job.role}
Cleaned JD:
{jd}
"""
    return call_llm(system=system, user=user, max_tokens=1000, temperature=0.0)


# ── 3. Company Research ──────────────────────────────────────────

def generate_company_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("research_checklist", "li_profile")
    system = f"""
## Role
You are an expert business researcher. 

## Task
Your task is to research a company and provide a summary of the companies history, evolution, funding, stage, and if public, key financials.
IMPORTANT: Every statement in your research must be grounded in fresh, complete URLs and citations following the citation rules below.
Links MUST be provided for all statements.

## Style 
- Write in clear, concise, high-signal bullet points for an executive, technical product manager. 
{target_audience}

## Requirements 
--BEGIN OUTPUT FORMAT (use bullets, remove all newlines/blank lines, cite sources, no headers, no preamble, no epilogue) --
- **Company snapshot:** [Content] (cite)
- **Culture signals:** [Content] (cite)
- **Org changes:** [Content] (cite)
- **Strategy alignment:** [Content] (cite)
- **Key financial metrics:** [Content] (cite)
--END OUTPUT FORMAT--

{writing_style}
IMPORTANT: Every statement in your research must be grounded in fresh, complete URLs and citations following the citation rules below.
Links MUST be provided for all statements.

"""
    jd = job.jd_cleaned or dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""
Research this company: {job.company} from the perspective of this role: {job.role}

"""
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


# ── 4. Leadership Research ───────────────────────────────────────

def generate_leadership_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("hm_research_checklist")
    system = f"""
## Role
You are a senior business researcher. 

## Task
Your task is to research a company and provide a summary of the company cultural maturity focusing on founders, execs, their work experience, life experience, and videos or posts.
EVERY statement in your research must be grounded in fresh, complete URLs and citations following the citation rules below.

{target_audience}

## Requirements
(per leader, cover the CEO / Founder, CTO, Head of Product/Engineering, and most likely hiring manager(s). Tag the most likely hiring managers with 👔. Look through multiple sources (Techcrunch, Verge, Crunchbase, LinkedIn, company blog, interviews, podcasts, videos, articles)

--BEGIN OUTPUT FORMAT--
### [Leader Name] ([Role])
- **Background:** [Prior roles, tenure, achievements] (cite)
- **Culture Stance:** [Explicit public stance on culture/WLB] (cite)
- **Maturity Signal:** [Evidence of leadership maturity] (cite)
- **Candidate Context:** [Relevance to candidate]
- **Sentiment:** [Glassdoor/blind sentiment] (cite)
- **Implications:** [What this implies for pace/style]
--END OUTPUT FORMAT--

{writing_style}
IMPORTANT: Every statement in your research must be grounded in fresh, complete URLs and citations following the citation rules below.
"""
    jd = job.jd_cleaned or dep_context.get("evidence_cleanup", job.jd_text or "")
    user = f"""
Research the leadership team at {job.company} and identify potential hiring manager(s) for this role: {job.role}
Cleaned Job Description:
{jd}
"""
    return call_llm(system=system, user=user, max_tokens=4000, temperature=0.3, use_web_search=True)


# ── 5. Strategy Research ─────────────────────────────────────────

def generate_strategy_research(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("strategy_checklist")
    system = f"""
## Role
You are a product strategy researcher expert in evaluating market positioning and product strategy fit.

## Task
Summarize product strategy and market positioning for this company, evaluating whether the strategy aligns with a Senior Principal PM's strengths in Applied AI, B2B SaaS, and scaling, and implies sustainable pace.

{target_audience}

## Requirements
- Source diversity: at least 4 sources across 3 distinct domains
- Competitor analysis: 3-5 direct or adjacent competitors with citations
- Differentiators: 2-3 specific, verifiable differentiators with citations
- Pricing: capture structure, levels, and strategic implications
- Recency: at least one source from the last 12 months
- Citations required and must be inline markdown links [domain](full, untrimmed, accurate url)

--BEGIN OUTPUT FORMAT--
- **Core Product:** [Description] (cite)
- **Target Customer:** [Description] (cite)
- **Differentiators:** [2-3 specific points] (cite each)
- **Competitors:** [3-5 with positioning] (cite)
- **Pricing:** [Structure + levels + implications] (cite)
- **Recent Changes:** [Key shifts in product/GTM] (cite)
- **PM Fit:** [How strategy aligns with Sr/Principal PM strengths]
--END OUTPUT FORMAT--

{writing_style}
"""
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
    system = f"""
## Role
You are a work-life balance and company culture researcher specializing in employee sentiment analysis.

## Task
Research work-life balance signals and employee sentiment for this company, emphasizing sustainability risks and health signals for a health-first Senior Principal PM.

{target_audience}

## Requirements
- Provide WLB rating (e.g., 3.8/5.0) if available; otherwise mark unavailable
- Summarize at least 2 contrasting themes (positive + negative) with evidence and citations
- Use at least 2 sources if Glassdoor is gated (Indeed, Comparably, Levels.fyi, Blind)
- Include recent sentiment shifts, layoffs, or restructuring signals
- Citations required and must be inline markdown links [domain](full, untrimmed, accurate url)

--BEGIN OUTPUT FORMAT--
- **WLB Rating:** [X.X/5.0 or "Unavailable"] (cite)
- **Positive Themes:** [2-3 bullets with evidence] (cite)
- **Negative Themes:** [2-3 bullets with evidence] (cite)
- **Recent Changes:** [Sentiment shifts, layoffs, restructuring] (cite)
- **Health Risk Assessment:** [Specific risks for health-first PM]
--END OUTPUT FORMAT--

{writing_style}
"""
    user = f"""Research work-life balance and employee reviews for {job.company}

Role context: {job.role}

Glassdoor Method:
{r['glassdoor_method']}
"""
    return call_llm(system=system, user=user, max_tokens=3000, temperature=0.3, use_web_search=True)


# ── 7. Scorecard: Health & Maturity (40pts) ──────────────────────

def generate_scorecard_health(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = f"""
## Role
You are a role-fit scoring expert using the Mnookin rubric to assess organizational and role health for a health-first Senior Principal PM.

## Task
Score the Health & Maturity dimension (40 points total) for this role, evaluating company stability, leadership quality, work-life balance sustainability, and culture alignment.

{target_audience}

## Requirements
- Score each sub-dimension (0-10 points) with explicit rationale grounded in evidence
- Every score must cite specific JD text, research findings, or review evidence
- Use the Mnookin rubric framework to ensure consistency and completeness
- Reference examples from deep analysis reference for output quality standards
- Format: bullet per sub-dimension with score, rationale, and key evidence citation
- Total score at the end: X/40

--BEGIN OUTPUT FORMAT--
**Company Maturity & Stability:** [X/10] — [Evidence with citation]
**Leadership Quality & Maturity:** [X/10] — [Evidence with citation]
**Work-Life Balance & Sustainability:** [X/10] — [Evidence with citation]
**Culture & Values Alignment:** [X/10] — [Evidence with citation]

**Total:** [X/40]

**Key Quote:** "[Specific JD or research quote capturing health signal/risk]"
--END OUTPUT FORMAT--

{writing_style}
"""
    # Cache large reference materials to reduce latency and cost
    cached_refs = f"""## Mnookin Rubric
{r['mnookin_rubric']}

## Deep Analysis Reference (quality standard)
{r['deep_analysis_reference']}"""

    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Score Health & Maturity (40pts) for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}
"""
    return call_llm_with_cache(system=system, user=user, cached_content=cached_refs, max_tokens=3000, temperature=0.2)


# ── 8. Scorecard: Role Fit (30pts) ───────────────────────────────

def generate_scorecard_role_fit(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = f"""
## Role
You are a role-fit scoring expert using the Mnookin rubric to assess alignment between a Senior Principal PM's strengths and role requirements.

## Task
Score the Role Fit dimension (30 points total) for this role, evaluating skill match, level & scope appropriateness, domain relevance, and growth potential.

{target_audience}

## Requirements
- Score each sub-dimension (0-10 points) with explicit rationale grounded in JD text and research
- Emphasize Applied AI, B2B SaaS, and scaling strengths from the target audience profile
- Every score must cite specific JD language or requirement
- Use the Mnookin rubric framework to ensure consistency
- Reference examples from deep analysis reference for quality standards
- Format: bullet per sub-dimension with score, rationale, and key evidence citation
- Total score at the end: X/30

--BEGIN OUTPUT FORMAT--
**Skill Match & Technical Alignment:** [X/10] — [Specific JD skills matched to experience]
**Level & Scope Fit:** [X/10] — [Evidence of Senior/Principal scope]
**Domain Relevance:** [X/10] — [B2B SaaS, AI/ML, Healthtech, Fintech match]
**Growth & Learning Potential:** [X/10] — [New challenges, not repeat play]

**Total:** [X/30]

**Key Quote:** "[JD quote showing role scope/complexity]"
--END OUTPUT FORMAT--

{writing_style}
"""
    # Cache large reference materials to reduce latency and cost
    cached_refs = f"""## Mnookin Rubric
{r['mnookin_rubric']}

## Deep Analysis Reference (quality standard)
{r['deep_analysis_reference']}"""

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
"""
    return call_llm_with_cache(system=system, user=user, cached_content=cached_refs, max_tokens=3000, temperature=0.2)


# ── 9. Scorecard: Personal + Bonus (30pts) ───────────────────────

def generate_scorecard_personal(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("mnookin_rubric", "deep_analysis_reference")
    system = f"""
## Role
You are a role-fit scoring expert using the Mnookin rubric to assess personal and motivational alignment with a role opportunity.

## Task
Score the Personal & Bonus dimension (30 points total) for this role, evaluating mission alignment, compensation/benefits attractiveness, location/flexibility fit, and unique opportunity factors.

{target_audience}

## Requirements
- Score each sub-dimension (0-10 points) with explicit rationale grounded in evidence
- Every score must cite specific research findings, JD language, or compensation data
- Use the Mnookin rubric framework for consistency
- Reference examples from deep analysis reference for quality standards
- Emphasize mission/motivation fit, location flexibility (health-first), unique network/brand/learning opportunities
- Format: bullet per sub-dimension with score, rationale, and key evidence citation
- Total score at the end: X/30

--BEGIN OUTPUT FORMAT--
**Mission & Personal Motivation:** [X/10] — [Why this mission matters]
**Compensation & Benefits Signals:** [X/10] — [Evidence from research]
**Location & Flexibility:** [X/10] — [Remote/SF alignment]
**Bonus Factors:** [X/10] — [Unique opportunities: network, learning, brand]

**Total:** [X/30]

**Key Quote:** "[Quote showing mission or unique opportunity]"
--END OUTPUT FORMAT--

{writing_style}
"""
    # Cache large reference materials to reduce latency and cost
    cached_refs = f"""## Mnookin Rubric
{r['mnookin_rubric']}

## Deep Analysis Reference (quality standard)
{r['deep_analysis_reference']}"""

    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Score Personal + Bonus (30pts) for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}
"""
    return call_llm_with_cache(system=system, user=user, cached_content=cached_refs, max_tokens=3000, temperature=0.2)


# ── 10. Between the Lines ────────────────────────────────────────

def generate_between_the_lines(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = f"""
## Role
You are a Strategic Product Analyst who decodes job descriptions to reveal true organizational nature, hidden dynamics, and potential friction points.

## Task
Analyze the subtext of this role to identify the true archetype, operating style, hidden risks, and political context that aren't explicitly stated in the JD.

{target_audience}

## Requirements
- **Archetype Classification:** MUST classify as Craftsperson (Builder), Operator (Scaler), or Visionary (Strategist)—can combine (e.g., "Visionary Operator")
- **Evidence-Based:** Ground all insights in JD text, company research, and leadership context
- **Specificity:** Identify concrete team dynamics, scope conflicts, or strategic pressures, not generic observations
- **Format:** Exactly 4 bullet points with bolded headers; max 40 words per bullet

--BEGIN OUTPUT FORMAT--
- **Archetype:** [Classification + 1-2 sentence interpretation grounded in JD]
- **Operating Style:** [How they work, what they value, specific constraints]
- **Hidden Risks:** [Concrete friction points, not generic warnings]
- **Political Context:** [Stage, funding pressure, leadership dynamics]
--END OUTPUT FORMAT--

{writing_style}

## Reference Examples (Quality Standards)

*Example 1 (YCharts):*
- **Archetype:** **The Technical Modernizer (Operator).** YCharts has the data; they need the intelligence. They need a PM who can turn raw financial time-series data into natural language answers.
- **Operating Style:** **Pragmatic Execution.** PE-owned (LLR Partners) means they care about ROI. They won't let you build "science projects." Every AI feature must drive retention or upsell.
- **Hidden Risks:** **Adoption Inertia.** Financial advisors are conservative. The risk is building a cool AI tool that no one trusts. You need to focus on "Explainability."
- **Political Context:** **Stable Growth.** CEO Sean Brown has led for 8+ years. No IPO pressure, just EBITDA growth.

*Example 2 (Ramp):*
- **Archetype:** **Visionary Craftsperson.** They are hiring a PM who can write code (or prompt-engineer it).
- **Operating Style:** **Velocity as a Feature.** Ramp wins by shipping faster than incumbents.
- **Hidden Risks:** **GM-like Accountability.** You are responsible for the P&L and headcount. In a 0->1 phase, you are the primary friction-remover for every edge case.
- **Political Context:** **Pre-IPO Sprints.** The pressure to show "AI Innovation" in every vertical is immense to juice valuation before the public offering.
"""
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Analyze the subtext for {job.company} — {job.role}

Cleaned JD:
{jd}

Context:
{dep_context.get('company_research', 'N/A')}
{dep_context.get('leadership_research', 'N/A')}

**Your Analysis:**
"""
    return call_llm(system=system, user=user, max_tokens=600, temperature=0.2)


# ── 11. Hours Estimate ───────────────────────────────────────────

def generate_hours_estimate(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("hours_drivers")
    system = f"""
## Role
You are an expert at estimating sustainable weekly work hours for tech roles, prioritizing health-first assessment.

## Task
Estimate weekly work hours for this role by triangulating from multiple signals (JD language, leadership expectations, company stage, team dynamics). Provide specific estimates (e.g., "50-55h"), not vague ranges.

{target_audience}

## Requirements
- Triangulate from at least 5 distinct signals: JD language/cadence, leadership background, WLB evidence, company stage, role scope
- Provide a specific estimate range (e.g., "52-60h/week"), not "50-70h"
- Assess confidence level (High/Medium/Low) based on evidence quality and consistency
- Every estimate must cite the JD evidence or research that supports it
- Identify upside risks that could push hours higher
- Use the hours drivers framework to structure analysis

--BEGIN OUTPUT FORMAT--
**Estimate:** [X-Y hours/week]
**Confidence:** [High/Medium/Low]

**Evidence by Signal:**
1. **JD Language:** [Sprint cadence, delivery signals] (cite)
2. **Leadership Background:** [Founder/exec expectations] (cite)
3. **Glassdoor/Reviews:** [WLB evidence] (cite)
4. **Company Stage:** [Funding/growth pressure] (cite)
5. **Role Scope:** [Cross-functional demands]

**Upside Risks:** [Factors that could push hours higher]
--END OUTPUT FORMAT--

{writing_style}
"""
    # Cache hours drivers framework to reduce latency and cost
    cached_refs = f"""## Hours Drivers Framework
{r['hours_drivers']}"""

    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Estimate weekly hours for {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Leadership Research:
{dep_context.get('leadership_research', 'N/A')}

Glassdoor Research:
{dep_context.get('glassdoor_research', 'N/A')}
"""
    return call_llm_with_cache(system=system, user=user, cached_content=cached_refs, max_tokens=2000, temperature=0.2)


# ── 12. Final Verdict ────────────────────────────────────────────

def generate_final_verdict(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile")
    system = f"""
## Role
You are a strategic talent synthesis expert who synthesizes all analysis dimensions into a decisive, quotable verdict.

## Task
Synthesize all analysis inputs (health, role fit, personal alignment, deep analysis, hours/risks) into a final recommendation with clear rationale and decision.

{target_audience}

## Requirements
- Sum all component scores to create Total Score (max 100)
- Synthesize 3 key hidden insights grounded in "Between the Lines" and deep analysis
- Identify 3 specific experience-to-need mappings that show unicorn fit
- Surface 1 primary caution or risk factor
- Provide decisive verdict: STRONG PURSUE / PURSUE / PASS / HARD PASS
- Use quotable, memorable synthesis statements
- Be concise: max 400 words total

--BEGIN OUTPUT FORMAT--
**Total Score:** [Sum]/100

**Between the lines:**
- **[Insight 1]:** [Explanation < 20 words]
- **[Insight 2]:** [Explanation < 20 words]
- **[Insight 3]:** [Explanation < 20 words]

**The Unicorn Match:**
- **[Match 1]:** [Your Experience] solves [Role Need].
- **[Match 2]:** [Your Experience] solves [Role Need].
- **[Match 3]:** [Your Experience] solves [Role Need].

**Caution:**
- [Risk warning < 20 words]

**Decision:** [STRONG PURSUE / PURSUE / PASS / HARD PASS]
--END OUTPUT FORMAT--

{writing_style}
"""
    user = f"""Synthesize final verdict for {job.company} — {job.role}

Inputs:
- Health Score: {dep_context.get('scorecard_health', '0')}
- Role Fit Score: {dep_context.get('scorecard_role_fit', '0')}
- Personal Score: {dep_context.get('scorecard_personal', '0')}
- Deep Analysis: {dep_context.get('between_the_lines', 'N/A')}
- Hours/Risk: {dep_context.get('hours_estimate', 'N/A')}
- Candidate Profile: {r['li_profile']}
"""
    return call_llm(system=system, user=user, max_tokens=600, temperature=0.2)
