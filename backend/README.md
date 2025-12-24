# ResumAI Backend

ResumAI Backend Service - An AI-powered resume optimization assistant API built with FastAPI.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Server**: Uvicorn
- **Configuration**: Pydantic Settings
- **HTTP Client**: HTTPX

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   └── routes/             # Route modules (implemented by RA-12)
│   │       └── __init__.py
│   │
│   ├── core/                   # Core configuration
│   │   ├── __init__.py
│   │   └── config.py           # Application settings (env variables)
│   │
│   ├── models/                 # Database models (reserved)
│   │   └── __init__.py
│   │
│   ├── schemas/                # Pydantic schemas (implemented by RA-12)
│   │   └── __init__.py
│   │
│   └── services/               # Business service layer
│       ├── __init__.py
│       └── llm/                # LLM service
│           ├── __init__.py
│           ├── base.py         # Abstract provider base class
│           └── factory.py      # Provider factory
│
├── venv/                       # Python virtual environment
├── requirements.txt            # Dependencies
├── run.py                      # Development server script
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

Rename the `env.exmaple` file to `.env file` or run below command
```bash
cp env.example .env
```

### 4. Start Server

```bash
python run.py
```

Server runs at http://localhost:8000 by default.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resume` | POST | Upload & parse resume file, initialize session |
| `/api/resume/analyze` | POST | Analyze resume and generate suggestions |
| `/api/resume/match` | POST | Calculate resume-job match score |
| `/api/resume/optimize` | POST | Optimize and rewrite resume |

### Directory Responsibilities

| Directory | Responsibility |
|-----------|----------------|
| `api/routes/` | HTTP routing, request validation, response formatting |
| `core/` | Application configuration, common dependencies |
| `models/` | Database ORM models (reserved) |
| `schemas/` | Pydantic request/response schema definitions |
| `services/` | Business logic, external service integrations |