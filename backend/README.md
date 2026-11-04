# ResumAI Backend

ResumAI Backend Service - An AI-powered resume optimization assistant API built with FastAPI.

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Configuration**: Pydantic Settings (`app/core/config.py`, read from `.env`)
- **LLM**: Google Gemini via LangChain (`langchain-google-genai`)
- **Storage**: Google Cloud Storage
- **Document parsing**: pypdf, python-docx
- **Tooling**: Poetry, Ruff, pytest (+ pytest-asyncio)

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, lifespan (starts job worker)
│   ├── api/routes/             # HTTP layer
│   │   ├── resumes.py          # upload / analyze / match / optimize
│   │   ├── interviews.py       # mock interview start / answer
│   │   └── jobs.py             # poll async job status
│   ├── core/
│   │   ├── config.py           # Application settings (env variables)
│   │   └── error_templates.py  # User-facing error messages
│   ├── schemas/                # Pydantic request/response schemas
│   └── services/
│       ├── resume_service.py   # Upload + retrieve resume content
│       ├── interview_service.py
│       ├── pdf_service.py      # Markdown → PDF
│       ├── jobs/               # In-memory job queue + result store
│       ├── llm/                # Provider base class, factory, Gemini provider, LLM service
│       ├── parsers/            # PDF / DOCX / DOC / TXT parsing
│       ├── prompt/             # Prompt templates and builders
│       ├── storage/            # GCS helpers
│       └── validators/         # File, session and content moderation checks
├── tests/                      # pytest suite
├── Dockerfile                  # Image used by Cloud Run
├── pyproject.toml / poetry.lock
├── run.py                      # Development server (hot reload)
└── env.example                 # Environment variables template
```

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install poetry
poetry install --no-root # Install dependencies from poetry.lock file
```

### 3. Configure Environment Variables

Rename the `env.example` file to `.env` file or run below command
```bash
cp env.example .env
```

GCS upload requires additional variables:
- `GCP_PROJECT_ID`
- `GCS_BUCKET_NAME`
- `GCS_OBJECT_PREFIX` (default: `resumes`)

### 4. Authentication for Local Development (Google Cloud)

Team members need to set up Application Default Credentials (ADC) on their local machines:

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
2. Run the following command in your terminal:
   ```bash
   gcloud auth application-default login
   ```
3. Follow the browser prompts to log in with your Google account.

This allows the backend to securely access GCS without sharing JSON key files.

### 5. Start Server

```bash
python run.py
```

Server runs at http://localhost:8000 by default.

### 6. Add a new package

If any new package needs to be added to this project, please
```bash
poetry add <package-name>
# this will automatically update poetry.lock and pyproject.toml
# and also install the package to your environment
```

## Running Tests and Lint

```bash
pytest          # all tests
ruff check .    # lint
```

## API Endpoints

Interactive docs: http://localhost:8000/api/docs

| Endpoint                  | Method | Description                                         |
| ------------------------- | ------ | --------------------------------------------------- |
| `/api/resumes/`           | POST   | Upload resume file, returns `session_id`            |
| `/api/resumes/analyze`    | POST   | Queue analysis job, returns `job_id` (202)          |
| `/api/resumes/match`      | POST   | Queue resume–job match job, returns `job_id` (202)  |
| `/api/resumes/optimize`   | POST   | Queue optimization job, returns `job_id` (202)      |
| `/api/interviews/start`   | POST   | Queue mock interview question generation (202)     |
| `/api/interviews/answer`  | POST   | Queue evaluation of one answer (202)               |
| `/api/jobs/{job_id}`      | GET    | Poll job status / result                            |
| `/health`                 | GET    | Health check                                        |

LLM work runs on a single background worker. The queue and results live in process memory (results kept for 30 minutes), so the service is designed to run as a single instance.

### Directory Responsibilities

| Directory     | Responsibility                                        |
| ------------- | ----------------------------------------------------- |
| `api/routes/` | HTTP routing, request validation, response formatting |
| `core/`       | Application configuration, common dependencies        |
| `schemas/`    | Pydantic request/response schema definitions          |
| `services/`   | Business logic, external service integrations         |