"""Cover letter section generation functions (8 sections).

Each function has the signature:
    def generate_xxx(job, refs, dep_context) -> GenerationResult

- job: JobResponse (has .company, .role, .jd_text, .jd_cleaned)
- refs: dict[str, str] from reference_loader
- dep_context: dict[str, str] of completed dependency section content
  For cover letter phase, dep_context includes ALL analysis sections too.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.claude_service import GenerationResult, call_claude
from app.services.reference_loader import load_references

if TYPE_CHECKING:
    from app.models import JobResponse


# ── 1. Pep Talk ──────────────────────────────────────────────────

def generate_cl_pep_talk(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    system = (
        "You are a career coach giving a pep talk before cover letter writing. "
        "Read between the lines of the JD and analysis to identify the hiring manager's "
        "implicit needs and fears. Explain why this candidate is the solution, grounded "
        "in their LinkedIn profile. Be energizing but honest."
    )
    r = load_references("li_profile")
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Pep talk for {job.company} — {job.role}

Cleaned JD:
{jd}

Final Verdict:
{dep_context.get('final_verdict', 'N/A')}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

Hours Estimate:
{dep_context.get('hours_estimate', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Produce:
1. **Read Between the Lines (HM's Implicit Needs/Fears):** What keeps the hiring manager up at night? What are they not saying but clearly need?
2. **Why You Are The Solution:** 2-3 strongest proof points from the LinkedIn profile that directly address these needs.
3. **Pep Talk:** Why this role is exciting, realistic hours expectations, potential impact, and what it means for the candidate's career.
"""
    return call_claude(system=system, user=user, max_tokens=3000, temperature=0.4)


# ── 2. Resume Headlines ─────────────────────────────────────────

def generate_cl_resume_headlines(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "approach")
    system = (
        "You are a resume headline expert for senior tech PMs. Create 5 headline options "
        "that position the candidate as a builder-PM, not just a manager.\n\n"
        "Constraints:\n"
        "- NO generic titles (e.g., 'Product Leader' alone)\n"
        "- NO 'Years of Experience' or 'X+ Years'\n"
        "- MUST include specific builder keywords: Hands-on, Shipping, Prototyping, Agentic, Evals, 0-to-1\n"
        "- MUST anchor with brand proof: Yelp, PayPal, Eventbrite, Grammarly, VuMedi\n"
        "- Under 250 characters each\n"
        "- Formatted as narrative value propositions"
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Create 5 resume headline options for {job.company} — {job.role}

Cleaned JD:
{jd}

LinkedIn Profile:
{r['li_profile']}

Approach:
{r['approach']}

Gold Standard Examples:
- "Hands-on building and shipping AI-driven B2B SaaS products. Launched multiple 0-to-1s at Yelp, Grammarly, Eventbrite, Vumedi, & PayPal, driving research, strategy, and scale."
- "Drives 0-to-1 applied AI by building trust with experts, hands-on prototype coding with Jupyter/Codex. Just launched internal AI deep research & sales preps."
- "A builder-PM with customer obsession from B2B SaaS (Grammarly, Vumedi, Yelp) with practical experience developing agentic AI workflows and navigating large-scale platforms (PayPal)."

Tailor each headline to emphasize different aspects relevant to this specific role.
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.5)


# ── 3. Introduction (3 options) ──────────────────────────────────

def generate_cl_intro(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cover_letter_template", "approach")
    system = (
        "You are a cover letter expert writing the introduction section. Write as a "
        "peer/consultant, not an applicant. Use the consultative approach: 'I understand "
        "your problem' rather than 'I fit the requirements.'\n\n"
        "Provide 3 distinct options (A, B, C) with different tones and angles.\n"
        "Add a WHY block under each explaining the reasoning.\n"
        "Strict grounding: every claim must be supported by the LinkedIn profile."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Write 3 intro options for cover letter to {job.company} — {job.role}

Cleaned JD:
{jd}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

Pep Talk:
{dep_context.get('cl_pep_talk', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Cover Letter Template:
{r['cover_letter_template']}

Approach:
{r['approach']}

Requirements:
- 2-3 sentences each
- Open with role + company + immediate value signal
- Each option should have a different angle (technical, mission-driven, problem-solving)
- Use contractions where natural
- Avoid em dashes; use commas or parentheses
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.5)


# ── 4. Problem Statement (2 options) ─────────────────────────────

def generate_cl_problem(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cover_letter_template")
    system = (
        "You are a cover letter expert writing the Problem Statement section. Frame it as "
        "a Strategic Hypothesis, not just pain points. Propose a shift (e.g., 'Moving from "
        "a scribe model to a care partner model').\n\n"
        "Provide 2 distinct options (A, B).\n"
        "Add a WHY block under each.\n"
        "Strict grounding in LinkedIn profile."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Write 2 problem statement options for cover letter to {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Strategy Research:
{dep_context.get('strategy_research', 'N/A')}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Cover Letter Template:
{r['cover_letter_template']}

Requirements:
- Reverse-engineer the business problem behind this hire
- Frame as a strategic hypothesis (State A to State B transition)
- 2-3 sentences each
- Consultative tone
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.5)


# ── 5. Proof Points (2 options) ──────────────────────────────────

def generate_cl_proof(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cover_letter_template")
    system = (
        "You are a cover letter expert writing the Proof Points section. Prove credibility "
        "with one insight + one measurable result.\n\n"
        "Provide 2 distinct options (A, B).\n"
        "Add a WHY block under each.\n"
        "Strict grounding: every claim must be in the LinkedIn profile. Do not invent."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Write 2 proof point options for cover letter to {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Cover Letter Template:
{r['cover_letter_template']}

Preferred story themes (use when relevant):
- VuMedi: AI/GenAI adoption, engagement, retention
- Grammarly: GenAI product strategy, embeddings, engagement
- Eventbrite: scaling systems, fintech, IPO readiness

Requirements:
- 2-3 sentences each
- Include measurable outcomes
- Connect proof to the specific role's needs
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.5)


# ── 6. Why Now (2 options) ───────────────────────────────────────

def generate_cl_why_now(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cover_letter_template")
    system = (
        "You are a cover letter expert writing the 'Why This Company / Why Now' section. "
        "Show personal motivation connected to a concrete product/market insight.\n\n"
        "Provide 2 distinct options (A, B).\n"
        "Add a WHY block under each.\n"
        "Strict grounding in LinkedIn profile."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Write 2 'why now' options for cover letter to {job.company} — {job.role}

Cleaned JD:
{jd}

Company Research:
{dep_context.get('company_research', 'N/A')}

Strategy Research:
{dep_context.get('strategy_research', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Cover Letter Template:
{r['cover_letter_template']}

Personal motivations (use when aligned):
- Passionate about building for customers who have a ripple impact on society
- Understanding users' underlying problems and motivations
- Learning and sharing insights

Requirements:
- Show genuine, specific interest in this company's product/market
- Connect to a concrete insight, not generic enthusiasm
- 2-3 sentences each
"""
    return call_claude(system=system, user=user, max_tokens=2000, temperature=0.5)


# ── 7. Closing (2 options) ───────────────────────────────────────

def generate_cl_closing(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cover_letter_template")
    system = (
        "You are a cover letter expert writing the Closing section. Close with a "
        "collaborative, low-pressure invite to compare notes.\n\n"
        "Provide 2 distinct options (A, B).\n"
        "Add a WHY block under each.\n"
        "One option should include a curiosity question on a key tradeoff this role "
        "would face."
    )
    jd = job.jd_cleaned or job.jd_text or ""
    user = f"""Write 2 closing options for cover letter to {job.company} — {job.role}

Cleaned JD:
{jd}

Between the Lines:
{dep_context.get('between_the_lines', 'N/A')}

LinkedIn Profile:
{r['li_profile']}

Cover Letter Template:
{r['cover_letter_template']}

Requirements:
- 1-2 sentences each
- Collaborative, peer-to-peer tone
- One option with a curiosity question about a key tradeoff
- Include a FOMO signal: what is uniquely valuable about how the candidate thinks
- Low-pressure call to action
"""
    return call_claude(system=system, user=user, max_tokens=1500, temperature=0.5)


# ── 8. Assembled Drafts (2 options) ──────────────────────────────

def generate_cl_assembled(job: JobResponse, refs: dict, dep_context: dict) -> GenerationResult:
    r = load_references("li_profile", "cl_best_practices")
    system = (
        "You are a cover letter assembler. Take the best section options and assemble "
        "two cohesive, send-ready drafts.\n\n"
        "Draft 1: 'Just Ship It' — full-length (150-250 words)\n"
        "Draft 2: 'Ship Fast' — half the length of Draft 1\n\n"
        "Both should flow naturally, not read like stitched-together sections.\n"
        "Include ATS keywords line.\n"
        "End with an empty FINAL VERSION section."
    )
    jd = job.jd_cleaned or job.jd_text or ""

    # Gather all CL section outputs
    cl_sections = ""
    for key in ["cl_intro", "cl_problem", "cl_proof", "cl_why_now", "cl_closing"]:
        content = dep_context.get(key, "")
        if content:
            cl_sections += f"\n\n## {key}\n{content}"

    user = f"""Assemble cover letter drafts for {job.company} — {job.role}

Cleaned JD:
{jd}

Resume Headlines:
{dep_context.get('cl_resume_headlines', 'N/A')}

Section Options:
{cl_sections}

LinkedIn Profile:
{r['li_profile']}

Best Practices:
{r['cl_best_practices']}

Instructions:
1. Pick the best option from each section and weave into a cohesive draft
2. Set TO line: named hiring manager if found, otherwise best guess labeled "(best guess)", otherwise "Hiring Manager"
3. Place KEYWORDS (ATS) immediately below the TO section — use exact job title plus 8-15 repeated JD terms
4. Draft 1 "Just Ship It": 150-250 words, full cohesive letter
5. Draft 2 "Ship Fast": half the length, same quality
6. End with empty ## FINAL VERSION section
7. Ensure no em dashes, use contractions naturally, vary sentence structure
"""
    return call_claude(system=system, user=user, max_tokens=4000, temperature=0.4)
