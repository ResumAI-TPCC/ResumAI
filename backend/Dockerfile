FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
EXPOSE 8000
CMD ["python", "run.py"]