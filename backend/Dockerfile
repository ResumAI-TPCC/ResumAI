FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
EXPOSE 8000
# Production server: no hot reload (run.py is for local development only).
# Cloud Run injects $PORT; default to 8000 for local `docker run`.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]