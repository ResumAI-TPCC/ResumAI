## Why

ResumAI has shipped MVP functionality (upload, analyze, match, optimize) and is live on GCP + Firebase. The next stage evolves it from a stateless session-based tool into a persistent, intelligent platform — adding identity, history, a structured AI pipeline, observability, and operational scalability to support growth and monetisation.

## What Changes

- **Identity layer**: Introduce Google OAuth 2.0 so users have accounts, persistent sessions, and history instead of ephemeral UUID sessions.
- **Persistent storage**: Replace session-only GCS state with a PostgreSQL database (Cloud SQL on GCP) storing user profiles, resume history, and job-match results.
- **AI pipeline modernisation**: Replace direct Gemini API calls with a LangChain-orchestrated pipeline, enabling structured chains, retrieval-augmented matching (pgvector), and future swappable models.
- **Semantic job matching**: Add pgvector extension to PostgreSQL for embedding-based job-description matching, replacing keyword-only comparison.
- **Performance & scalability**: Decouple long-running analysis/optimize/match jobs from the HTTP request cycle using a job queue (Cloud Tasks or Celery + Redis) with async worker processing.
- **Observability**: Integrate LangSmith for AI pipeline tracing and usage analytics; use Langflow for visual agent workflow design.
- **Frontend**: New marketing landing page and a complete UI/UX refresh of the analysis dashboard.
- **Secrets management**: Migrate all secrets from GitHub Secrets and `.env` files to Google Cloud Secret Manager for unified, auditable credential management.
- **Infrastructure as Code**: All GCP infrastructure (Cloud Run, Cloud SQL, Cloud Tasks, Secret Manager, GCS, IAM) defined as Terraform in a dedicated `resumai-infra` repository with GCS remote state.
- **CI/CD decoupling**: Source code repository handles only CI (lint, test, build, push Docker image to Artifact Registry); the IaC repository handles CD (pull image by digest, apply Terraform, inject configs) — no application secrets ever leave GCP.
- **GCS file tracking**: Every file stored in GCS is registered in a PostgreSQL `gcs_files` table linked to the owning user, enabling per-user file inventory, expiry alignment, and orphan prevention.

## Capabilities

### New Capabilities

- `google-oauth`: Google OAuth 2.0 login, JWT session management, user profile persistence, and logout flow.
- `user-profiles-db`: PostgreSQL (Cloud SQL) schema for users, resume history, analysis results, and job-match history; Cloud SQL Auth Proxy integration.
- `landing-page-ui`: Marketing landing page (hero, features, CTA) and a redesigned analysis dashboard with improved UX, component library refresh, and responsive layout.
- `structured-agent`: LangChain-based agent replacing direct Gemini calls — structured chains for analyze, optimize, and match; tool-use patterns; prompt versioning.
- `pgvector-job-matching`: Semantic job-description matching using pgvector on Cloud SQL — resume and JD embeddings, cosine similarity scoring, ranked results.
- `job-queue-worker`: Async job processing via Cloud Tasks (or Celery + Redis); HTTP endpoints return a `job_id` immediately; clients poll or receive webhook callbacks.
- `langsmith-monitoring`: LangSmith project integration for chain tracing, token usage, latency, and error tracking across all LLM operations.
- `langflow-workflow`: Langflow integration for visual design and export of agent workflows; exported flows importable into LangChain pipeline.
- `gcp-secret-manager`: Migration of all credentials (`GEMINI_API_KEY`, `GCP_*`, DB passwords) from GitHub Secrets / `.env` to GCP Secret Manager; backend reads secrets at startup via `google-cloud-secret-manager`.
- `infra-as-code`: Terraform modules in a dedicated `resumai-infra` repository defining all GCP resources; Workload Identity Federation for keyless GitHub Actions auth; GCS-backed remote state.
- `ci-cd-decoupling`: GitHub Actions CI workflow in source repo (lint → test → build → push image tag); IaC repo CD workflow receives image digest and applies infrastructure changes via Terraform.
- `gcs-file-tracking`: Dedicated `gcs_files` PostgreSQL table linking every GCS object to a user profile with metadata (path, size, MIME type, expiry); upload handler writes DB record atomically with GCS upload.

### Modified Capabilities

- `resume-processing`: Core analyze/optimize/match endpoints change from synchronous response to async job-queue pattern — response contract changes from result payload to `{ job_id, status_url }`. **BREAKING**

## Impact

- **Backend**: New auth middleware, DB models (SQLAlchemy + Alembic), LangChain service layer replaces `llm/gemini_provider.py`, job dispatcher, Secret Manager config loader, `gcs_files` registry table and upload service update.
- **Frontend**: New pages (landing, auth callback, job history), polling/websocket for async job results, OAuth redirect flow.
- **Infrastructure**: Cloud SQL instance, Cloud Tasks queue, Secret Manager secrets, Artifact Registry repository — all managed via Terraform in `resumai-infra` repo; Dockerfile updates; Workload Identity Federation replaces service account key files in CI.
- **New repository**: `resumai-infra` (separate git repo) containing all Terraform modules and the CD workflow.
- **Dependencies**: `langchain`, `langchain-google-genai`, `langsmith`, `pgvector`, `sqlalchemy`, `alembic`, `google-cloud-secret-manager`, `google-cloud-tasks`; frontend: OAuth client library.
- **Breaking change**: `/analyze`, `/match`, `/optimize` response shape changes to async job model — requires frontend update and any API consumers to adapt.
