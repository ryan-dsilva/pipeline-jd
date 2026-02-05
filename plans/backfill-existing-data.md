# Backfill Existing Data into PocketBase

## Goal
Import existing role analyses, cover letters, and evidence files from `/Users/ryan/Next/` into PocketBase so historical work is accessible in the app.

## Data Sources

### 1. Role Analyses (`/Users/ryan/Next/role-analyses/`)
- **Root files**: `score-{N}__hours-{H}__Complete__{Company}__{Role}__{date}__posted-{date}.md`
- **Subdirectories**: `Applied/`, `Not Interested/` — same filename format with status prefixes
- **Metadata parsed from filename**: score, hours, company, role, date_added, date_posted
- **Pipeline stage derived from location**:
  - Root → `"analyzed"` (or `"ready"` if matching cover letter exists)
  - `Applied/` → `"applied"`
  - `Not Interested/` → `"ignored"`

### 2. Cover Letters (`/Users/ryan/Next/cover-letters/`)
- Same directory structure: root, `Applied/`, `Not Interested/`
- Same filename pattern (without `posted-` suffix sometimes)
- Matched to role analyses by `(company, role)` tuple

### 3. Evidence Files (`/Users/ryan/Next/role-analyses/evidence/`)
- `jd-evidence__{Company}__{Role}__{date}.md`
- Contains `**URL:**` line (→ `jd_url`) and `## Full JD Text` section (→ `jd_text`)
- Matched to role analyses by `(company, role)` tuple

## Section Mapping

The markdown files are monolithic — each contains all sections concatenated. The backfill script needs to split them into individual sections matching the app's `section_key` values.

### Role Analysis → Section Keys
The role analysis markdown has these H2 headings that map to section keys:

| Markdown H2 / Content Block | Section Key | Phase |
|---|---|---|
| Full file content (evidence file) | `evidence_cleanup` | analysis |
| `## PART 1: IMMEDIATE DISQUALIFIERS` | `gate_check` | analysis |
| `### Leadership Experience & Stance` (inside Part 3) | `leadership_research` | analysis |
| `### Company Research` or company-related content in Part 3 | `company_research` | analysis |
| `### Strategy` or strategy content in Part 3 | `strategy_research` | analysis |
| `### Glassdoor & WLB Signal` (in verdict block) | `glassdoor_research` | analysis |
| `### SECTION 1: HEALTH & MATURITY` (inside Part 2) | `scorecard_health` | analysis |
| `### SECTION 2: ROLE FIT` (inside Part 2) | `scorecard_role_fit` | analysis |
| `### SECTION 3: SKILL MATCH` or `PERSONAL` (inside Part 2) | `scorecard_personal` | analysis |
| `### Between the Lines` (in verdict block) | `between_the_lines` | analysis |
| `### Hours Estimate` or hours content in verdict | `hours_estimate` | analysis |
| `## FINAL VERDICT` | `final_verdict` | analysis |

### Cover Letter → Section Keys

| Markdown H2 | Section Key | Phase |
|---|---|---|
| `## RESUME HEADLINE OPTIONS` | `cl_resume_headlines` | cover_letter |
| `## PEP TALK & DEEP DIVE` | `cl_pep_talk` | cover_letter |
| `## SECTION 1 — INTRO` | `cl_intro` | cover_letter |
| `## SECTION 2 — PROBLEM UNDERSTANDING` | `cl_problem` | cover_letter |
| `## SECTION 3 — PROOF & OUTCOMES` | `cl_proof` | cover_letter |
| `## SECTION 4 — WHY THIS COMPANY` | `cl_why_now` | cover_letter |
| `## SECTION 5 — CLOSING` | `cl_closing` | cover_letter |
| `## JUST SHIP IT` through end (or `## FINAL VERSION`) | `cl_assembled` | cover_letter |

## Script: `backend/scripts/backfill.py`

### Behavior
1. **Scan** all three directories for markdown files
2. **Parse filenames** to extract metadata (score, hours, company, role, dates, stage)
3. **Match** evidence files and cover letters to role analyses by `(company, role)`
4. **Parse markdown** content — split on H2/H3 headings to extract individual sections
5. **Create jobs** in PocketBase via SDK (with slug, company, role, jd_url, jd_text, score, hours, verdict, pipeline_stage, date_added, date_posted)
6. **Create sections** for each parsed block (with job relation, section_key, phase, status="complete", content_md)
7. **Skip duplicates** — check if a job with the same slug already exists before creating
8. **Log** results: created, skipped, failed

### CLI Interface
```bash
cd backend
python -m scripts.backfill                    # dry run (print what would be created)
python -m scripts.backfill --commit           # actually write to PocketBase
python -m scripts.backfill --commit --clear   # wipe existing data first, then import
```

### Filename Parsing
```
score-82__hours-40__Complete__UpCodes__Product-Manager-Core__2026-01-26__posted-2026-01-11.md
  │         │         │         │              │                │              │
  score     hours     status    company        role             date_added     date_posted
```

- Split on `__` (double underscore)
- `score-N` → extract N
- `hours-N` → extract N
- Company and Role have hyphens replaced with spaces for display
- `posted-unknown` → date_posted = None

### Evidence File Parsing
- Extract URL from `**URL:** <url>` line → `jd_url`
- Extract everything after `## Full JD Text` → `jd_text`
- The cleaned-up version (from the role analysis itself) → `jd_cleaned`

### Section Splitting Strategy
- Split the role analysis markdown on `^## ` boundaries
- Within Part 2 (Scorecard), split on `^### SECTION` boundaries
- Within Part 3 (Research), split on `^### ` boundaries
- For cover letters, split on `^## ` boundaries — each maps directly to a section key
- Use regex matching on heading text to identify which section key each block belongs to

### Edge Cases
- Some files have `Draft__` prefix → pipeline_stage = "analyzing" (incomplete)
- Some files in `Applied/` have `Applied_Jan8_Waiting_` prefix → strip prefix, stage = "applied"
- Files without a matching evidence file → jd_url and jd_text will be empty
- Files without a matching cover letter → only analysis sections are created
- The `## FINAL VERDICT` section in the role analysis contains embedded subsections (Between the Lines, Glassdoor, Hours) that need to be extracted separately AND the full verdict block stored as `final_verdict`

## Estimate
~30-40 jobs to import based on the file count across all directories.
