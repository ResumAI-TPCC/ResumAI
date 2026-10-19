# ResumAI

ResumAI is an AI-powered resume optimization assistant (monorepo containing backend and frontend).

Users upload a resume and can:
- **Analyze** it and get prioritized improvement suggestions
- **Match** it against a job description (or job title / company) and get a score breakdown
- **Optimize** it into a rewritten resume, downloadable as PDF
- **Practice a mock interview** with questions tailored to the resume and JD, with per-answer feedback

## Architecture

```
┌─────────────────┐   /api/**   ┌──────────────────────────────┐
│ React + Vite    │ ──────────▶ │ FastAPI (Cloud Run)          │
│ (Firebase       │  (Firebase  │  routes → services → LLM     │
│  Hosting)       │   rewrite)  │  in-memory job queue + worker│
└─────────────────┘             └───────┬──────────────┬───────┘
                                        │              │
                                  Google Cloud     Gemini (via
                                  Storage          LangChain)
```

- **Backend** (`backend/`): FastAPI, Python 3.10+, Poetry. Uploads go to GCS keyed by a `session_id` (no user accounts; sessions expire after 24 h). LLM work runs asynchronously: endpoints return `202 Accepted` with a `job_id`, and the client polls `GET /api/jobs/{job_id}`.
- **Frontend** (`frontend/`): React 18, Vite, Tailwind CSS 3. Single-page layout; state lives in `pages/ResumeAnalysisPage.jsx` and is persisted to `localStorage`.
- **Docs** (`doc/`): design doc and QA reports.

### API overview

All endpoints are under `/api` and return `{ code, status, data }`. Interactive docs are served at `/api/docs` when the backend is running.

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/api/resumes/` | Upload a resume (PDF/DOCX/DOC/TXT, max 5 MB), returns `session_id` |
| POST | `/api/resumes/analyze` | Queue an analysis job |
| POST | `/api/resumes/match` | Queue a resume–job match job |
| POST | `/api/resumes/optimize` | Queue an optimization job (result is a base64 PDF) |
| POST | `/api/interviews/start` | Queue mock interview question generation |
| POST | `/api/interviews/answer` | Queue evaluation of one interview answer |
| GET | `/api/jobs/{job_id}` | Poll job status and result |
| GET | `/health` | Health check |

## Getting started (for collaborators)

### Backend (development)

1. Create and activate a Python virtualenv inside `backend/`.

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

2. Install dependencies and configure env

```bash
pip install poetry
poetry install --no-root
cp env.example .env
```

Fill in `GEMINI_API_KEY`, `GCP_PROJECT_ID` and `GCS_BUCKET_NAME` in `.env`. For local GCS access, set up Application Default Credentials:

```bash
gcloud auth application-default login
```

3. Start the backend (development, hot reload on http://localhost:8000)

```bash
python run.py
```

### Frontend (development)

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

## Testing & linting

Run these before pushing; CI runs the same checks on every PR to `develop` / `main`.

| | Lint | Tests |
| - | ---- | ----- |
| Backend (`backend/`) | `ruff check .` | `pytest` |
| Frontend (`frontend/`) | `npm run lint` | `npm test` |

## Deployment

Pushing to `develop` deploys to the QA environment automatically (Cloud Run `test-service` + Firebase `platform_site`). Production (`prod-service` + `app_site`) is deployed by manually running the **Production CD** workflow on `main`. See `.github/workflows/`.

## Contributing

- Branch from `develop` and open PRs against `develop`.
- Fill in the PR template (`.github/pull_request_template.md`), including the Jira ticket number (`RA-xxx`).
- Add dependencies with `poetry add <pkg>` / `npm install <pkg>` so lockfiles stay in sync.
- Follow existing code style and run linters/tests before pushing.

## More info

- Backend details: [`backend/README.md`](backend/README.md)
- Frontend details: [`frontend/README.md`](frontend/README.md)
- Design doc: [`doc/design.md`](doc/design.md)
