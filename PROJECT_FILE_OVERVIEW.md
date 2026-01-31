# Project File Overview

This file summarizes what each tracked file/folder is for. Keep it updated whenever files are added, removed, or change purpose.

## Quick Setup
1. Copy `.env.example` to `backend/.env` and fill in your keys.
2. Install backend deps: `cd backend && pip install -r requirements.txt`.
3. Install frontend deps: `cd frontend && npm install`.
4. Start everything: `./start.sh` (starts PocketBase, backend, frontend).

## Environment Variables
- `ANTHROPIC_API_KEY`: Anthropic API key used for extraction and chat.
- `POCKETBASE_URL`: PocketBase base URL (for example `http://127.0.0.1:8090`).

## Root
- `start.sh`: starts PocketBase (if present), backend (uvicorn), and frontend (Vite), opens the Vite URL, and tails logs.
- `stop.sh`: stops processes recorded in `.pids` and cleans up the pidfile.
- `run-tests.sh`: runs backend pytest (optionally paid Anthropic tests) and frontend Vitest, logging to `test-runs/`.
- `PROJECT_FILE_OVERVIEW.md`: this file.
- `.pids`: runtime pidfile written by `start.sh` (not source-controlled).
- `.vite_output`: Vite dev server log output (not source-controlled).
- `.DS_Store`: macOS metadata (not source-controlled).

## backend/
- `backend/.env`: local environment variables for backend (PocketBase URL, Anthropic key).
- `backend/pyproject.toml`: backend Python project configuration.
- `backend/requirements.txt`: backend Python dependencies.
- `backend/app/__init__.py`: package marker for FastAPI app.
- `backend/app/main.py`: FastAPI app setup, CORS, and router registration.
- `backend/app/config.py`: settings loader (env vars).
- `backend/app/database.py`: PocketBase client, record helpers, and section upsert utilities.
- `backend/app/models.py`: Pydantic models and constants for API payloads.
- `backend/app/extraction.py`: Claude-based JD company/role extraction.
- `backend/app/services/claude_service.py`: synchronous Claude call wrapper + result model.
- `backend/app/services/pipeline_executor.py`: DAG executor for analysis/cover-letter sections + DB updates.
- `backend/app/services/assembler.py`: deterministic cover-letter assembly helpers.
- `backend/app/services/reference_loader.py`: loads reference markdowns from `references/`.
- `backend/app/routers/jobs.py`: job CRUD + extraction + stage updates.
- `backend/app/routers/pipeline.py`: start analysis/cover-letter pipeline + SSE status stream.
- `backend/app/routers/sections.py`: CRUD/regeneration/locking for sections + definitions endpoint.
- `backend/app/routers/chat.py`: streaming Claude chat endpoint with section context.
- `backend/app/sections/__init__.py`: package marker for section generators.
- `backend/app/sections/config.py`: section definitions, dependencies, and phases.
- `backend/app/sections/registry.py`: maps section keys to generation functions.
- `backend/app/sections/analysis.py`: analysis section generation prompts.
- `backend/app/sections/cover_letter.py`: cover letter section generation prompts.
- `backend/tests/conftest.py`: pytest fixtures/config.
- `backend/tests/test_*.py`: backend unit/integration tests.
- `backend/.pytest_cache/`: pytest cache (not source-controlled).

## frontend/
- `frontend/README.md`: default Vite template README (not yet project-specific).
- `frontend/package.json`: frontend dependencies and scripts.
- `frontend/package-lock.json`: lockfile for npm dependencies.
- `frontend/tsconfig.json`: base TS config.
- `frontend/tsconfig.app.json`: TS config for app build.
- `frontend/tsconfig.node.json`: TS config for tooling.
- `frontend/eslint.config.js`: ESLint configuration.
- `frontend/vite.config.ts`: Vite configuration.
- `frontend/vitest.config.ts`: Vitest configuration.
- `frontend/index.html`: Vite HTML entry.
- `frontend/src/main.tsx`: React entrypoint.
- `frontend/src/App.tsx`: app shell and routing.
- `frontend/src/index.css`: global styles.
- `frontend/src/setupTests.ts`: test setup.
- `frontend/src/lib/api.ts`: API client helpers.
- `frontend/src/lib/types.ts`: shared frontend types.
- `frontend/src/hooks/useApi.ts`: API hook wrapper.
- `frontend/src/hooks/useSSE.ts`: SSE hook for pipeline/chat streaming.
- `frontend/src/pages/AllJobsPage.tsx`: page listing all jobs.
- `frontend/src/pages/JobsPage.tsx`: page for active pipeline jobs.
- `frontend/src/pages/NewJobPage.tsx`: page to create a new job.
- `frontend/src/pages/RoleDetailPage.tsx`: job detail page with sections.
- `frontend/src/components/ChatPanel.tsx`: chat UI for job-specific assistant.
- `frontend/src/components/JobsTable.tsx`: jobs list table component.
- `frontend/src/components/NewJDForm.tsx`: form for creating jobs.
- `frontend/src/components/PipelineProgress.tsx`: pipeline progress UI.
- `frontend/src/components/SectionCard.tsx`: section display card.
- `frontend/src/components/SectionEditor.tsx`: markdown editor for sections.
- `frontend/src/components/TabNav.tsx`: navigation tabs.
- `frontend/src/components/NewJDForm.test.tsx`: component tests for job form.
- `frontend/dist/`: build output (generated, not source-controlled).
- `frontend/node_modules/`: npm dependencies (generated, not source-controlled).
- `frontend/.gitignore`: frontend-specific ignore rules.

## references/
- `references/*.md`: research templates, checklists, resumes, and cover-letter references used by pipeline sections.

## backlog/
- `backlog/backfill-existing-data.md`: backlog note for data backfill.

## pocketbase/
- `pocketbase/pocketbase`: PocketBase binary.
- `pocketbase/README.md`: how to apply migrations and recreate schema locally.
- `pocketbase/pb_data/data.db`: main PocketBase SQLite database (not source-controlled).
- `pocketbase/pb_data/auxiliary.db`: PocketBase auxiliary SQLite database (not source-controlled).
- `pocketbase/pb_data/types.d.ts`: auto-generated TypeScript type definitions for PocketBase schema.
- `pocketbase/pb_migrations/001_initial_schema.js`: initial PocketBase collection schema migration.
- `pocketbase/pb_migrations/1769792972_updated_jobs.js`: jobs collection migration update.
- `pocketbase/pb_migrations/1769802039_updated_jobs.js`: jobs collection migration update.

## test-runs/
- `test-runs/*.log`: timestamped test run logs produced by `run-tests.sh`.
