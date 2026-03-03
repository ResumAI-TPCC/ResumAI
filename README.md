# ResumAI

ResumAI is an AI-powered resume optimization assistant (monorepo containing backend and frontend).

Overview
- Backend: FastAPI service that parses, analyzes, matches and optimizes resumes.
- Frontend: React + Vite app for upload and analysis UI.

Repository layout
- `backend/` — FastAPI backend service (LLM integration, file & storage services).
- `frontend/` — React + Vite frontend (Tailwind CSS).
- `doc/` — design and QA docs.

Getting started (for collaborators)

Backend (development)

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

3. Start the backend (development)

```bash
python run.py
```

Notes:
- Google Cloud Storage upload requires `GCP_PROJECT_ID`, `GCS_BUCKET_NAME` and (optionally) `GCS_OBJECT_PREFIX`.
- For local GCS access, set up Application Default Credentials with `gcloud auth application-default login`.

Frontend (development)

```bash
cd frontend
npm ci
npm run dev
```

Project conventions
- Backend: FastAPI app entry is `backend/app/main.py` and service code lives under `backend/app/services/`.
- Frontend: React app entry is `frontend/src/main.jsx` and components under `frontend/src/components/`.

Testing & linting
- Backend tests live in `backend/tests/` and use pytest.
- Frontend tests live in `frontend/src/tests/` and use Jest.

Contributing
- Follow existing code style and run linters/tests before pushing.
- Use the PR templates in `.github/PULL_REQUEST_TEMPLATE/` when opening pull requests.

Where to look for more info
- Backend README: `backend/README.md`
- Frontend README: `frontend/README.md`

If you need help, ping the team in our usual channel.
