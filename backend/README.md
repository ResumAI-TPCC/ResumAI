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
│   │   └── routes/             # Route modules
│   │       ├── __init__.py     # Route aggregation
│   │       └── chat.py         # Chat API
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
│   │   └── chat.py             # Chat request/response schemas
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
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp env.example .env
# Edit .env file to configure required parameters
```

### 4. Start Server

```bash
python run.py
```

Server runs at http://localhost:8000 by default.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/chat/completions` | POST | Chat completion |
| `/api/v1/chat/completions/stream` | POST | Streaming chat completion |
| `/api/v1/docs` | GET | Swagger API documentation |
| `/api/v1/redoc` | GET | ReDoc API documentation |

## LLM Provider Architecture

The project uses the Abstract Factory pattern for LLM Providers, making it easy to integrate different LLM services.

### Core Interface

```python
class BaseLLMProvider(ABC):
    """LLM Provider abstract base class"""

    @abstractmethod
    async def chat(self, messages, temperature, max_tokens) -> LLMResponse:
        """Synchronous chat completion"""
        pass

    @abstractmethod
    async def chat_stream(self, messages, temperature, max_tokens) -> AsyncIterator[str]:
        """Streaming chat completion"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name"""
        pass
```

### Adding a New Provider

1. Create a new file under `app/services/llm/`, e.g., `openai_provider.py`
2. Inherit from `BaseLLMProvider` and implement all abstract methods
3. Register the provider at application startup:

```python
from app.services.llm import register_provider
from app.services.llm.openai_provider import OpenAIProvider

register_provider("openai", OpenAIProvider)
```

4. Set environment variable `LLM_PROVIDER=openai`

## Development Guide

### Directory Responsibilities

| Directory | Responsibility |
|-----------|----------------|
| `api/routes/` | HTTP routing, request validation, response formatting |
| `core/` | Application configuration, common dependencies |
| `models/` | Database ORM models (reserved) |
| `schemas/` | Pydantic request/response schema definitions |
| `services/` | Business logic, external service integrations |

### Code Standards

- Use Type Hints for type annotations
- Follow PEP 8 code style
- Async-first approach (async/await)
