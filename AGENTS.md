# AGENTS.md

This file guides agentic coding agents working in this repository.

## Build/Lint/Test Commands

### Backend (Python)
```bash
cd backend
python -m pytest tests/ -v                    # Run all tests (excludes paid Anthropic API)
python -m pytest tests/ -v -m "not anthropic_api"  # Explicit exclude paid tests
python -m pytest tests/test_jobs.py::test_create_job_saves_and_extracts -v  # Single test
python3 -m uvicorn app.main:app --reload --port 8000  # Start dev server
```

### Frontend (TypeScript/React)
```bash
cd frontend
npm run build                                # Build production bundle
npm run lint                                 # Run ESLint
npx vitest run                               # Run all tests
npx vitest run -t "test name"                # Run single test by name
npm run dev                                  # Start Vite dev server
```

### Unified Test Runner
```bash
./run-tests.sh                               # Run all backend + frontend tests (excludes paid)
./run-tests.sh paid                          # Run all tests including Anthropic API calls
```

## Plan Management

### Plan Storage
All execution plans must be stored in the `plans/` subfolder at the repository root. Each plan should be a descriptive markdown file (e.g., `plans/2026-01-31-add-playwright-tests.md`).

### Plan Structure
Every plan file must include:

1. **Task Summary**: Brief description of what will be accomplished
2. **Stages Checklist**: A checklist for every major stage of work
3. **Progress Tracking**: Each checklist item must be marked as complete (✓) when finished

### Checklist Example
```markdown
## Task: Add Playwright E2E Tests

### Stages Checklist

- [ ] Stage 1: Install Playwright and set up configuration
  - [ ] Install @playwright/test
  - [ ] Install browser binaries
  - [ ] Create playwright.config.ts
  - [ ] Create tests/e2e/ directory structure

- [ ] Stage 2: Write tests for job creation flow
  - [ ] Create job-creation.spec.ts
  - [ ] Implement test for valid job submission
  - [ ] Implement test for validation errors

- [ ] Stage 3: Write tests for pipeline execution
  - [ ] Create pipeline-execution.spec.ts
  - [ ] Implement test for analysis phase
  - [ ] Implement test for cover letter phase

- [ ] Stage 4: Document and verify
  - [ ] Update AGENTS.md with Playwright usage
  - [ ] Run all E2E tests successfully
```

### Resuming Work
When resuming work in a new session:
1. Read the plan file from `plans/`
2. Review completed stages (marked with ✓)
3. Start from the first incomplete stage
4. Update the checklist as you complete each stage

This approach allows stopping at any point and resuming later without losing progress.

## Context Usage Tracking

### Monitor Context Usage
Agents must continuously monitor context usage during execution and provide updates to the user at these thresholds:
- **30%**: "Context usage at 30%. Consider clearing if task is unrelated to previous work."
- **50%**: "Context usage at 50%. Recommend clearing or compacting context."
- **70%**: "Context usage at 70%. Strongly recommend clearing context."

### Context Clearance Before New Tasks
When a user requests a new task:
1. **Assess task similarity**: Compare new task with previous work in the current session
2. **Ask user if task is very different**: Use the `question` tool with dropdown options

Example prompt:
```
The new task ("Add search functionality to jobs page") seems significantly different from previous work ("Setting up Playwright tests"). 

Should I clear the context before starting?
```

Dropdown options:
- **Yes, clear context** - Start fresh with no previous context
- **No, continue** - Keep existing context (may be more expensive)
- **Compact context** - Keep only essential files, clear conversation history

### Context Management Commands
When context reaches thresholds or user requests clearance:
- Use dropdown options via `question` tool to ask user preference
- Explain trade-offs (accuracy vs cost)
- Provide context summary before clearing if user requests

## Current Code Style Guidelines

### Python
- Add `from __future__ import annotations` at top of every file
- Use `snake_case` for variables/functions, `PascalCase` for classes
- Import order: standard library → third-party → local modules
- Pydantic models for API payloads with `@field_validator` decorators
- Use `Optional[str]` for nullable fields
- Section comments: `# ── SECTION NAME ──`
- HTTPException for API errors
- Async functions with `async def` and `await` for I/O operations

### TypeScript/React
- Functional components with hooks only (no class components)
- `kebab-case` for component files (e.g., `jobs-table.tsx`)
- `PascalCase` for component exports and types
- Explicit `Props` interfaces for component props
- Tailwind CSS for styling with `className` prop
- React Router for navigation with `useNavigate` hook
- Type-only imports: `import type { T }` from "module"
- Inline type definitions: `Record<string, string>`

### Frontend Patterns
- API client in `lib/api.ts` uses `request<T>()` wrapper with consistent error handling
- Custom hooks in `hooks/` (useApi, useSSE) for reusable logic
- State management: `useState` for local state, `useMemo` for computed values
- Components in `components/ui/` for reusable UI elements

### Backend Patterns
- Routers in `app/routers/` with prefixes and tags (e.g., `APIRouter(prefix="/api/jobs")`)
- PocketBase client via `from app.database import pb`
- `record_to_dict()` helper to convert PocketBase records to dicts
- `sanitize_pb_value()` to escape filter string values
- `upsert_section()` for creating/updating sections by (job, section_key)

## Testing - Non-Negotiable Priority

### Core Principle
All key functionality must have at least one test. Complex logic gets multiple tests. Always write tests when adding features.

### Backend Testing (pytest)
- Use fixtures in `conftest.py` for reusable test data (`_make_job_record`, `_make_section_record`)
- Mark expensive tests with `@pytest.mark.anthropic_api`
- Test both success and error paths
- Mock PocketBase client at import sites (see `conftest.py` `mock_pb` fixture)

### Frontend Testing (vitest + @testing-library/react)
- Co-locate test files with components (e.g., `Component.test.tsx`)
- Test user interactions and state changes, not just rendering
- Mock external dependencies (API calls, router) with `vi.mock()`

### E2E Testing (Playwright - RECOMMENDED ADDITION)
Critical user flows should be tested with Playwright to avoid manual testing:
- Job creation flow (NewJobPage)
- Pipeline execution and status updates (RoleDetailPage)
- Section editing and locking
- Stage updates and navigation

**Priority:** Add Playwright before major feature development. Create `tests/e2e/` directory and install Playwright:
```bash
npm install -D @playwright/test
npx playwright install
```

### Good vs Better Testing Examples

```python
# Good: Tests happy path only
def test_create_job(client, mock_pb):
    response = client.post("/api/jobs", json={...})
    assert response.status_code == 201

# Better: Tests success + duplicate URL + validation
def test_create_job_saves_and_extracts(client, mock_pb, mock_extraction):
    response = client.post("/api/jobs", json={...})
    assert response.status_code == 201
    data = response.json()
    assert data["extraction_status"] == "complete"
    mock_extraction.assert_called_once()

def test_create_job_duplicate_url_rejected(client, mock_pb):
    # Setup duplicate, test 409 response
    existing_job = Mock(id="existing_job_id")
    mock_pb.collection().get_first_list_item.return_value = existing_job
    response = client.post("/api/jobs", json={...})
    assert response.status_code == 409
```

```typescript
// Good: Tests rendering only
it("renders form", () => {
  render(<NewJDForm />);
  expect(screen.getByLabelText(/JD URL/i)).toBeInTheDocument();
});

// Better: Tests interaction + validation + API call
it("creates job on valid submit", async () => {
  const mockCreate = vi.mocked(createJob);
  render(<NewJDForm />);

  await userEvent.type(screen.getByLabelText(/JD URL/i), "https://example.com");
  await userEvent.type(screen.getByLabelText(/JD Text/i), "Job text...");
  await userEvent.click(screen.getByRole("button", { name: /Create Job/i }));

  expect(mockCreate).toHaveBeenCalledWith({
    jd_url: "https://example.com",
    jd_text: "Job text..."
  });
});
```

## Code Quality Improvements

### Priority Order: Testing > Type Safety > Error Handling > Architecture

### Python Tools
- Add **ruff** for linting (fastest, combined linting/formatting, fewest false positives)
- Consider mypy for type checking
- Add coverage reporting: `pytest --cov=app --cov-report=html`

### TypeScript Improvements
- Enable stricter ESLint type rules in `eslint.config.js`
- Use type-only imports where possible
- Standardize error handling patterns across API client

### Good vs Better Code Examples

```python
# Good: Inline string sanitization
query = f"filter = '{jd_url}'"

# Better: Reusable utility function (already exists in app.database)
query = f"filter = '{sanitize_pb_value(jd_url)}'"

# Good: Separate update calls
pb.collection("jobs").update(id, {"company": company})
pb.collection("jobs").update(id, {"role": role})

# Better: Single update with multiple fields
pb.collection("jobs").update(id, {"company": company, "role": role})
```

```typescript
// Good: Multiple useState calls
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// Better: Enum-based status (clearer state machine)
type Status = "idle" | "loading" | "success" | "error";
const [status, setStatus] = useState<Status>("idle");
const [error, setError] = useState<string | null>(null);

// Good: Ad-hoc fetch with inline error handling
const res = await fetch("/api/jobs");
if (!res.ok) throw new Error("Failed");

// Better: Centralized API client (already exists in lib/api.ts)
const jobs = await listJobs();  // Has consistent error handling
```

## File Organization Guidelines

### Create New Files When
- Utility function appears in 3+ places → `lib/utils.ts` (frontend) or `services/utils.py` (backend)
- New API domain → `routers/new_domain.py` (backend)
- Reusable UI component → `components/ui/NewComponent.tsx`
- New page/route → `pages/NewPage.tsx` (frontend)

### Extend Existing When
- Same domain data models → extend existing Pydantic models in `app/models.py`
- Related test functionality → add to existing test file
- Logically grouped routes → add to existing router file

### Shared Constants
Keep pipeline stages and verdicts synchronized between backend and frontend:
- Backend: `app/models.py` (PIPELINE_STAGES, VERDICTS)
- Frontend: `src/lib/types.ts` (PIPELINE_STAGES, VERDICTS)
