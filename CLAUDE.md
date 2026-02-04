# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Pipeline JD** is a full-stack job application analysis and cover letter generation tool. It extracts job details from JD URLs, analyzes them against personal qualifications and company culture, and generates tailored cover letter options.

**Tech Stack:**
- **Backend:** FastAPI (Python) with PocketBase SQLite database
- **Frontend:** React 19 + TypeScript with Tailwind CSS
- **AI:** Anthropic Claude API for all generation and analysis
- **Infrastructure:** Vite dev server, Vitest for testing

## Build & Development Commands

### Quick Start
```bash
./start.sh          # Start PocketBase, backend, frontend (opens localhost:5173)
./kill.sh           # Stop all processes
```

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt                              # Install deps
python3 -m uvicorn app.main:app --reload --port 8000       # Dev server
python -m pytest tests/ -v                                   # Run all tests
python -m pytest tests/ -v -m "not anthropic_api"           # Skip paid API tests
python -m pytest tests/test_jobs.py::test_name -v           # Single test
```

### Frontend (TypeScript/React)
```bash
cd frontend
npm install                        # Install deps
npm run dev                       # Start Vite dev server
npm run build                     # Production build
npm run lint                      # Run ESLint
npx vitest run                    # Run all tests
npx vitest run -t "test name"     # Single test by name
```

### Unified Testing
```bash
./run-tests.sh          # All tests (excludes paid Anthropic API calls)
./run-tests.sh paid     # All tests including Anthropic API
```

### Environment Setup
1. Copy `backend/.env.example` to `backend/.env`
2. Set `ANTHROPIC_API_KEY` and `POCKETBASE_URL` (e.g., `http://127.0.0.1:8090`)
3. PocketBase migrations auto-apply on startup from `pocketbase/pb_migrations/`

## Architecture Overview

### High-Level Flow
1. **Job Intake:** User submits JD URL → backend extracts company/role via Claude
2. **Analysis Phase:** DAG executor runs 13 analysis sections (research, scoring, verdict)
3. **Cover Letter Phase:** 7 standalone sections generate multiple options per section
4. **Assembly:** Cover letter sections combine into 2 complete draft options
5. **Editing:** User can lock/edit sections, regenerate unlocked ones

### Backend Architecture

**Core Layer (app/):**
- `main.py` - FastAPI setup with CORS, router registration
- `config.py` - Environment variable loader
- `models.py` - Pydantic request/response models and constants (PIPELINE_STAGES, VERDICTS)
- `database.py` - PocketBase client, record helpers, section upsert utilities

**Services Layer:**
- `llm_service.py` - Synchronous Claude API wrapper with result models
- `pipeline_executor.py` - **DAG executor** respecting section dependencies, runs ready sections concurrently, streams SSE events
- `assembler.py` - Deterministic cover-letter assembly (combines 4 sections into complete draft)
- `reference_loader.py` - Caches reference markdown files from `references/` directory

**Sections System (app/sections/):**
- `config.py` - Section definitions with metadata: 13 analysis sections (with DAG dependencies), 7 cover letter sections
- `registry.py` - Maps section keys to generation functions
- `analysis.py` - Analysis section generation functions and prompts
- `cover_letter.py` - Cover letter section generation functions and prompts

**Routers (app/routers/):**
- `jobs.py` - Job CRUD, JD extraction, stage updates
- `pipeline.py` - Start analysis/cover-letter phases, stream SSE events
- `sections.py` - CRUD for sections (get, regenerate locked/unlocked), definitions endpoint
- `chat.py` - Streaming Claude chat with section context

### Section Dependency Graph (Analysis Phase)

```
evidence_cleanup (order 20)
    ↓
gate_check (order 7)
    ├─ company_research (order 8)
    ├─ leadership_research (order 9)
    ├─ strategy_research (order 10)
    └─ glassdoor_research (order 11)
        ├─ scorecard_health (order 3)
        ├─ scorecard_role_fit (order 4)
        └─ scorecard_personal (order 5)
        ├─ between_the_lines (order 2)
        └─ hours_estimate (order 6)
            ↓
        final_verdict (order 1)
```

All dependencies must be satisfied before a section runs. The executor runs ready sections **concurrently** via asyncio. Cover letter sections have no dependencies and all run in parallel.

### Frontend Architecture

**Pages:**
- `AllJobsPage.tsx` - List all jobs (archived + active)
- `JobsPage.tsx` - List active jobs in pipeline
- `NewJobPage.tsx` - Create new job with JD URL/text
- `RoleDetailPage.tsx` - Job detail view with sections, chat, regenerate controls

**Hooks:**
- `useApi.ts` - Wrapper for API calls with error handling
- `useSSE.ts` - Server-Sent Events for pipeline/chat streaming

**Components:**
- `JobsTable.tsx` - Jobs list table with stage/verdict display
- `NewJDForm.tsx` - Form for job creation
- `SectionEditor.tsx` - Markdown editor with lock/unlock toggle
- `SectionPanel.tsx` - Display section content (analysis/cover letter)
- `SectionCard.tsx` - Card wrapper for section display
- `ChatPanel.tsx` - Chat assistant with job context
- `PipelineProgress.tsx` - Pipeline execution progress UI
- `TabNav.tsx` - Tab navigation

**Data Layer:**
- `lib/api.ts` - Centralized API client with consistent error handling (`request<T>()`)
- `lib/types.ts` - Shared types and constants (must sync with backend models.py)

## Key Patterns & Conventions

### Pipeline Execution
- **Pipeline phases:** "analysis" → "cover_letter" (sequential, frontend controls transitions)
- **Sections have states:** pending, running, complete, error, locked (locked sections skip regeneration)
- **DAG executor:** Waits for all dependencies before starting a section, runs ready sections concurrently
- **SSE streaming:** Pipeline router streams `PipelineEvent` objects (section updates, errors)

### Database Schema (PocketBase)
- `jobs` - Main job record (jd_url, jd_text, company, role, extraction_status, analysis_stage, cover_letter_stage, final_verdict)
- `sections` - Section content (job_id, section_key, content, locked_at)

### API Response Pattern
All responses use consistent models in `app/models.py`:
- `JobResponse` - Job with all metadata
- `SectionResponse` - Section with content and lock state
- `PipelineEvent` - SSE events (section_key, status, content, error)

### Constants Sync (CRITICAL)
Must keep synchronized between backend and frontend:
- **Backend:** `app/models.py` → PIPELINE_STAGES, VERDICTS, SECTION_KEYS
- **Frontend:** `src/lib/types.ts` → Same constants
Mismatch causes UI/logic bugs.

## Testing Strategy

### Priority: All Key Functionality Needs Tests
- Happy path required for every feature
- Error paths for operations with failure modes (API calls, validation, DAG execution)
- Use fixtures for reusable test data

### Backend Testing (pytest)
- Fixtures in `conftest.py`: `_make_job_record()`, `_make_section_record()`
- Mark expensive tests: `@pytest.mark.anthropic_api`
- Mock PocketBase at import (see `conftest.py`)
- Example: Test job creation includes extraction trigger, validation, duplicate detection

### Frontend Testing (vitest + @testing-library/react)
- Co-locate tests: `Component.test.tsx` next to component
- Test user interactions, not just rendering
- Mock API calls with `vi.mock()`
- Example: Test form submission triggers API call with correct payload

### E2E Testing (Playwright - RECOMMENDED)
Critical flows should use Playwright to avoid manual testing:
- Job creation flow (NewJobPage)
- Pipeline execution (RoleDetailPage with sections)
- Section editing and locking
- Chat with job context

To add: `npm install -D @playwright/test && npx playwright install`

## Code Style Guidelines

### Python
```python
from __future__ import annotations  # Top of every file
from app.services import helper     # Local imports last

class MyModel:                       # PascalCase for classes
    pass

def my_function(arg: str) -> str:   # snake_case for functions/variables
    pass

# Use this for section organization:
# ── SECTION NAME ──

# Pydantic models with validators:
from pydantic import BaseModel, field_validator

class JobRequest(BaseModel):
    url: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        # validation logic
        return v

# Async I/O:
async def fetch_data():
    result = await some_async_op()
    return result
```

### TypeScript/React
```typescript
// Type-only imports
import type { Job, Section } from "@/lib/types";

// PascalCase for components/types, kebab-case for files
export interface JobsTableProps {
  jobs: Job[];
  onSelect: (job: Job) => void;
}

export function JobsTable({ jobs, onSelect }: JobsTableProps) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="grid gap-4">
      {jobs.map(job => (
        <button key={job.id} onClick={() => onSelect(job)}>
          {job.company}
        </button>
      ))}
    </div>
  );
}

// Centralized API client (always use request<T>):
const job = await request<JobResponse>('GET', `/api/jobs/${jobId}`);

// React patterns:
// - useState for local state
// - useMemo for expensive computed values
// - useApi hook for API calls with error handling
// - useSSE hook for streaming (pipeline, chat)
```

## Debugging & Troubleshooting

### Common Issues

**PocketBase Connection:**
- Check `POCKETBASE_URL` in `backend/.env`
- Verify PocketBase running: `curl http://127.0.0.1:8090`
- Check migrations applied: `pocketbase/pb_migrations/` should all have run

**Frontend API Errors:**
- Check CORS in `app/main.py` allows `localhost:5173`
- Verify backend running on port 8000
- Check `lib/api.ts` error handling logs in console

**Section Generation Timeout:**
- Check `ANTHROPIC_API_KEY` is valid
- Monitor `pipeline_executor.py` logs for dependency issues
- Verify all section functions registered in `sections/registry.py`

**DAG Deadlock (Dependency Bug):**
- Check `sections/config.py` dependencies form no cycles
- Verify all `depends_on` section keys exist
- Test with: `python -m pytest tests/test_pipeline_executor.py -v`

## File Organization

### When to Create New Files
- New utility function used in 3+ places → `backend/app/services/utils.py` or `frontend/src/lib/utils.ts`
- New API domain (not covered by existing routers) → `backend/app/routers/new_domain.py`
- Reusable UI component → `frontend/src/components/ui/NewComponent.tsx`
- New page/route → `frontend/src/pages/NewPage.tsx`

### When to Extend Existing Files
- Related Pydantic models → add to `backend/app/models.py`
- Related test data → add to `backend/tests/conftest.py`
- Related routes → add to existing router file in `backend/app/routers/`
- Related components → group in `frontend/src/components/`

## Git Workflow

### Branches
- All work happens on feature branches from `main`
- Plan work in `plans/` directory with checklist tracking
- Commit messages describe "why", not just "what"

### Before Committing
1. Run tests: `./run-tests.sh`
2. Check linting: `cd frontend && npm run lint`
3. Verify no secrets in diff (`ANTHROPIC_API_KEY`, etc.)

### Plan Files
Store all execution plans in `plans/` with:
- **Task Summary:** What will be accomplished
- **Stages Checklist:** Major work milestones (mark ✓ when complete)
- **Progress Tracking:** Update checklist as you work

Example:
```markdown
## Task: Add Chat Feature

### Stages Checklist
- [x] Stage 1: Design chat API endpoint
- [ ] Stage 2: Implement streaming backend
- [ ] Stage 3: Build chat UI component
- [ ] Stage 4: Test end-to-end
```

Allows resuming work later by reading the plan and checking completed stages.

## Important Reminders

1. **Sync Constants:** Always keep PIPELINE_STAGES and VERDICTS in sync between `app/models.py` and `src/lib/types.ts`
2. **Test New Features:** No excuses—write tests alongside implementation
3. **DAG Integrity:** Validate section dependencies have no cycles before running pipeline
4. **API Consistency:** Always use `request<T>()` wrapper in frontend for consistent error handling
5. **Reference Caching:** `load_references()` caches by filename—safe to call multiple times
6. **Section Locking:** Locked sections skip regeneration; unlocked re-run when pipeline restarts
