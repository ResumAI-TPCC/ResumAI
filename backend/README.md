# ResumAI Backend

ResumAI Backend Service - An AI-powered resume optimization assistant API built with FastAPI.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Server**: Uvicorn
- **Configuration**: Pydantic Settings
- **HTTP Client**: HTTPX
- **Task Queue**: Celery + Redis (optional, for async processing)

## Architecture

### Synchronous Mode (Default)
All requests are processed synchronously. Suitable for development and low-traffic deployments.

### Async Queue Mode (Optional)
Uses Celery + Redis for background job processing. Recommended for production and high-traffic scenarios.

Benefits:
- Non-blocking API responses
- Better scalability
- Automatic retry on failures
- Job status tracking

To enable: Set `USE_ASYNC_QUEUE=true` in `.env` and start the Celery worker.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   └── routes/             # Route modules
│   │       ├── __init__.py
│   │       ├── resumes.py      # Resume endpoints (sync + async)
│   │       └── jobs.py         # Job status query endpoint
│   │
│   ├── core/                   # Core configuration
│   │   ├── __init__.py
│   │   └── config.py           # Application settings (env variables)
│   │
│   ├── models/                 # Database models (reserved)
│   │   └── __init__.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   └── resume_schema.py    # Request/Response schemas
│   │
│   └── services/               # Business service layer
│       ├── __init__.py
│       ├── llm/                # LLM service
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract provider base class
│       │   └── factory.py      # Provider factory
│       │
│       ├── queue/              # Async task queue (NEW)
│       │   ├── __init__.py
│       │   ├── celery_app.py   # Celery configuration
│       │   ├── job_store.py    # Redis job state management
│       │   └── tasks.py        # Background tasks
│       │
│       └── ...
│
├── tests/                      # Test suite
├── venv/                       # Python virtual environment
├── poetry.lock                 # Locked dependency list
├── pyproject.toml              # Dependencies
├── run.py                      # Development server script
├── run_worker.py               # Celery worker script (NEW)
├── env.example                 # Environment variables template
└── README.md
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

### 6. Start Celery Worker (Optional - for async queue mode)

If using async queue mode, you also need to start the Celery worker:

```bash
# Terminal 1: Start Redis (if not already running)
redis-server

# Terminal 2: Start Celery Worker
python run_worker.py
```

Or use the Celery CLI directly:
```bash
celery -A app.services.queue.celery_app worker --loglevel=info
```

### 7. Add a new package

If any new package needs to be added to this project, please
```bash
poetry add <package-name>
# this will automatically update poetry.lock and pyproject.toml
# and also install the package to your environment
```

## API Endpoints

### Resume Endpoints

| Endpoint                      | Method | Description                                      |
| ----------------------------- | ------ | ------------------------------------------------ |
| `/api/resumes`                | POST   | Upload resume, initialize session                |
| `/api/resumes/analyze`        | POST   | Analyze resume (sync)                            |
| `/api/resumes/analyze/async`  | POST   | Analyze resume (async, returns job_id)           |
| `/api/resumes/match`          | POST   | Match resume with JD (sync)                      |
| `/api/resumes/match/async`    | POST   | Match resume with JD (async, returns job_id)     |
| `/api/resumes/optimize`       | POST   | Optimize resume (sync)                           |
| `/api/resumes/optimize/async` | POST   | Optimize resume (async, returns job_id)          |

### Job Status Endpoint

| Endpoint              | Method | Description                             |
| --------------------- | ------ | --------------------------------------- |
| `/api/jobs/{job_id}`  | GET    | Query job status and result             |

### Job Status Values

| Status     | Description                          |
| ---------- | ------------------------------------ |
| `queued`   | Job is waiting to be processed       |
| `processing` | Job is currently being executed    |
| `completed` | Job finished successfully           |
| `failed`   | Job failed, see error message        |

### Async Flow Example

```bash
# 1. Start async analysis
curl -X POST http://localhost:8000/api/resumes/analyze/async \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id"}'

# Response: {"code": 202, "status": "accepted", "data": {"job_id": "abc-123"}}

# 2. Poll job status
curl http://localhost:8000/api/jobs/abc-123

# Response (processing):
# {"code": 200, "data": {"job_id": "abc-123", "status": "processing", ...}}

# Response (completed):
# {"code": 200, "data": {"job_id": "abc-123", "status": "completed", "result": {...}}}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_ASYNC_QUEUE` | Enable async queue mode | `false` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/0` |
| `JOB_RESULT_EXPIRY_HOURS` | Job result TTL in Redis | `24` |

### Directory Responsibilities

| Directory     | Responsibility                                        |
| ------------- | ----------------------------------------------------- |
| `api/routes/` | HTTP routing, request validation, response formatting |
| `core/`       | Application configuration, common dependencies        |
| `models/`     | Database ORM models (reserved)                        |
| `schemas/`    | Pydantic request/response schema definitions          |
| `services/`   | Business logic, external service integrations         |
| `services/queue/` | Celery configuration, job store, background tasks |