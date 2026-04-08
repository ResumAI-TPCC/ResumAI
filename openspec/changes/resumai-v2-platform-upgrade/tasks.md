## 1. Infrastructure & Secrets Migration

- [ ] 1.1 Provision Cloud SQL (PostgreSQL 15 + pgvector extension) instance in GCP project
- [ ] 1.2 Create all required secrets in GCP Secret Manager (`GEMINI_API_KEY`, `GCS_BUCKET_NAME`, `DATABASE_URL`, `LANGCHAIN_API_KEY`, `JWT_SECRET`)
- [ ] 1.3 Add `google-cloud-secret-manager` to backend Poetry dependencies
- [ ] 1.4 Update `get_settings()` in `core/config.py` to detect GCP environment and fetch secrets from Secret Manager; retain `.env` fallback for local dev
- [ ] 1.5 Update GitHub Actions deploy workflow to use only `GOOGLE_APPLICATION_CREDENTIALS` (or Workload Identity Federation); remove individual app secrets
- [ ] 1.6 Create Cloud Tasks queue in GCP (`resumai-jobs` queue)
- [ ] 1.7 Write `docker-compose.langflow.yml` for local Langflow design sessions

## 2. Database Foundation

- [ ] 2.1 Add `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pgvector` to backend Poetry dependencies
- [ ] 2.2 Create SQLAlchemy async engine factory in `backend/app/core/database.py` with Cloud SQL Auth Proxy socket + TCP fallback
- [ ] 2.3 Define SQLAlchemy ORM models: `User`, `RefreshToken`, `ResumeSession`, `AnalysisResult`, `MatchResult`, `Job`
- [ ] 2.4 Initialise Alembic (`alembic init`); configure `env.py` to use async engine and import all models
- [ ] 2.5 Generate initial Alembic migration for all tables including `vector(768)` column on `ResumeSession`
- [ ] 2.6 Add `ivfflat` index on `resume_sessions.content_embedding` in the migration
- [ ] 2.7 Verify `alembic upgrade head` applies cleanly on a local PostgreSQL instance

## 3. Google OAuth Integration (Backend)

- [ ] 3.1 Add `authlib` (or `google-auth`) and `python-jose` to backend dependencies
- [ ] 3.2 Implement `GET /api/auth/google/login` — generate authorization URL with PKCE + CSRF `state` cookie
- [ ] 3.3 Implement `GET /api/auth/google/callback` — validate `state`, exchange code, upsert `User`, issue JWT + refresh token as HTTP-only cookies
- [ ] 3.4 Implement `POST /api/auth/refresh` — validate refresh token, issue new access token, rotate refresh token in DB
- [ ] 3.5 Implement `POST /api/auth/logout` — revoke refresh token, clear cookies
- [ ] 3.6 Add FastAPI auth middleware that validates JWT from cookie and populates `request.state.user_id`
- [ ] 3.7 Apply auth middleware to `/api/resumes/*` and `/api/jobs/*` routes
- [ ] 3.8 Write pytest tests for login, callback (valid + invalid state), refresh, and logout flows

## 4. LangChain Pipeline & Structured Agent

- [ ] 4.1 Add `langchain`, `langchain-google-genai`, `langsmith` to backend Poetry dependencies
- [ ] 4.2 Create `backend/app/services/llm/langchain_provider.py` implementing `BaseLLMProvider` with LCEL chains for `analyze`, `optimize`, `match`
- [ ] 4.3 Convert existing prompt strings in `prompt/builder.py` and `prompt/templates.py` to `ChatPromptTemplate` objects
- [ ] 4.4 Add `with_retry` (max 3, exponential back-off) wrapper to each chain; map 429 → `LLMRateLimitException`, 400 → `LLMInvalidRequestException`
- [ ] 4.5 Register `LangChainProvider` in `factory.py` as `"langchain"`; add `LLM_MODEL_NAME` setting to `config.py`
- [ ] 4.6 Configure LangSmith tracing: read `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` from settings; set `run_name` tag per operation
- [ ] 4.7 Update `.env.example` with `LANGCHAIN_*` variables (all optional, default off)
- [ ] 4.8 Write integration tests for `LangChainProvider` using recorded fixtures (no live Gemini calls)
- [ ] 4.9 Create `backend/app/services/llm/flows/` directory; commit initial Langflow-exported JSON flow (can be placeholder)

## 5. Async Job Queue

- [ ] 5.1 Add `google-cloud-tasks` to backend Poetry dependencies
- [ ] 5.2 Create `backend/app/services/job_service.py` — `dispatch_job(job_type, payload) -> job_id`; creates `Job` row in DB and enqueues Cloud Tasks HTTP task
- [ ] 5.3 Create `backend/app/api/routes/jobs.py` — `GET /api/jobs/{job_id}` returning status/result; enforce ownership check
- [ ] 5.4 Create `backend/app/api/routes/worker.py` — `POST /internal/jobs/{job_id}/process` (Cloud Tasks target); implement idempotent handlers for `analyze`, `optimize`, `match`
- [ ] 5.5 Refactor `POST /api/v2/resumes/analyze` to use `job_service.dispatch_job`; return HTTP 202 with `{ job_id, status_url }`
- [ ] 5.6 Refactor `POST /api/v2/resumes/match` to use `job_service.dispatch_job`; return HTTP 202
- [ ] 5.7 Refactor `POST /api/v2/resumes/optimize` to use `job_service.dispatch_job`; return HTTP 202; worker stores PDF in GCS and writes signed URL to job result
- [ ] 5.8 Verify duplicate task delivery idempotency with a test that calls the worker handler twice for the same `job_id`
- [ ] 5.9 Keep v1 sync endpoints (`/api/resumes/analyze`, `/api/resumes/match`, `/api/resumes/optimize`) operational; add deprecation warning header

## 6. pgvector Semantic Matching

- [ ] 6.1 Add `langchain-google-genai` embeddings interface usage for `text-embedding-004`; verify 768-dimension output
- [ ] 6.2 Implement `EmbeddingService` in `backend/app/services/embedding_service.py` — `generate_embedding(text) -> list[float]`
- [ ] 6.3 Add embedding generation to the upload worker (after resume parse): store result in `ResumeSession.content_embedding`
- [ ] 6.4 Add JD embedding generation to the match worker; store in `MatchResult.jd_embedding`
- [ ] 6.5 Implement cosine similarity query using `<=>` pgvector operator in `MatchResult` creation; store `semantic_score` (0–1)
- [ ] 6.6 Include `semantic_score` in the match job result payload returned by `GET /api/jobs/{job_id}`
- [ ] 6.7 Write unit tests for `EmbeddingService` with a mocked embedding model

## 7. Frontend — Auth & Landing Page

- [ ] 7.1 Add `VITE_GOOGLE_CLIENT_ID` to `frontend/src/config/env.js` (`ENV` object)
- [ ] 7.2 Create landing page component (`frontend/src/pages/LandingPage.jsx`) — hero, feature highlights, "Sign in with Google" CTA; redirect to `/dashboard` if authenticated
- [ ] 7.3 Implement `GET /api/auth/google/login` redirect in `frontend/src/utils/api.js`
- [ ] 7.4 Create `AuthCallbackPage.jsx` to handle `/auth/callback` route (store auth state, redirect to `/dashboard`)
- [ ] 7.5 Add React Router routes: `/` → `LandingPage`, `/auth/callback` → `AuthCallbackPage`, `/dashboard` → `ResumeAnalysisPage` (protected)
- [ ] 7.6 Implement `ProtectedRoute` wrapper that redirects to `/` if unauthenticated
- [ ] 7.7 Add logout button to dashboard header calling `POST /api/auth/logout`

## 8. Frontend — Dashboard Redesign & Async Jobs

- [ ] 8.1 Redesign `ResumeAnalysisPage.jsx` to three-panel layout: sidebar (history), main (upload/status), results panel
- [ ] 8.2 Implement job polling hook `useJobPoller(jobId)` — polls `GET /api/jobs/{job_id}` every 2 s; max 60 polls; returns `{ status, result, error }`
- [ ] 8.3 Update `api.js` analyze/match/optimize calls to handle HTTP 202 + `job_id` response; wire to `useJobPoller`
- [ ] 8.4 Add progress indicator (spinner + elapsed time) while job is pending/processing
- [ ] 8.5 Add poll timeout error state with "Retry" button
- [ ] 8.6 Implement `HistorySidebar` component — fetches `GET /api/resumes/history`; clicking an item loads stored results from DB
- [ ] 8.7 Ensure responsive layout: sidebar collapses to drawer below 768 px breakpoint
- [ ] 8.8 Update Jest tests for `FileUpload`, `AnalysisOutput` to reflect async job flow

## 9. Resume History API

- [ ] 9.1 Implement `POST /api/resumes/` (v2) — persist `ResumeSession` row linked to `user_id` after GCS upload
- [ ] 9.2 Implement `GET /api/resumes/history` — return paginated list of `ResumeSession` rows for authenticated user
- [ ] 9.3 Implement `GET /api/resumes/{session_id}/analysis` — return latest `AnalysisResult` for the session; enforce ownership
- [ ] 9.4 Write pytest tests for history list (empty, paginated) and analysis retrieval (owned, not owned)

## 10. Testing & Validation

- [ ] 10.1 Run `pytest` (full backend suite) — all tests pass
- [ ] 10.2 Run `ruff check .` — no lint errors
- [ ] 10.3 Run `npm test` (frontend Jest suite) — all tests pass
- [ ] 10.4 Run `npm run lint` — no ESLint errors
- [ ] 10.5 Smoke-test the full auth flow end-to-end in staging: login → upload → analyze (async) → poll → view result → logout
- [ ] 10.6 Verify idempotent job handler with duplicate Cloud Tasks delivery in staging
- [ ] 10.7 Verify Secret Manager secret loading in Cloud Run staging deployment
- [ ] 10.8 Verify `alembic upgrade head` is included in CI deploy step and runs cleanly
- [ ] 10.9 Verify source repo CI does NOT update Cloud Run (inspect workflow run logs; no gcloud/terraform commands present)
- [ ] 10.10 Verify IaC repo CD applies Terraform and updates Cloud Run revision after a source repo image push
- [ ] 10.11 Verify `gcs_files` record is created on upload and soft-delete removes both DB record and GCS object
- [ ] 10.12 Run orphan-scan job once in staging and confirm no orphans exist after a clean upload/delete cycle

## 11. Infrastructure as Code (`resumai-infra` repository)

- [ ] 11.1 Create `resumai-infra` git repository with directory structure: `modules/compute/`, `modules/database/`, `modules/storage/`, `modules/secrets/`, `modules/iam/`, `modules/tasks/`, `envs/staging/`, `envs/prod/`
- [ ] 11.2 Create GCS bucket `resumai-tf-state` with versioning enabled for Terraform remote state
- [ ] 11.3 Configure Terraform backend in `resumai-infra` root: GCS backend pointing to `resumai-tf-state`
- [ ] 11.4 Write `modules/iam/` Terraform: create service accounts for API, worker, Cloud SQL Auth Proxy; configure Workload Identity Federation pool and providers for source repo and IaC repo GitHub Actions
- [ ] 11.5 Write `modules/storage/` Terraform: GCS application bucket, lifecycle rule (delete after `SESSION_EXPIRY_HOURS + 1 h`), CORS config, IAM bindings
- [ ] 11.6 Write `modules/database/` Terraform: Cloud SQL instance (PostgreSQL 15), database, users, pgvector extension enablement, Auth Proxy service account binding
- [ ] 11.7 Write `modules/secrets/` Terraform: Secret Manager secret resource declarations for all required secrets (values pushed separately via `gcloud secrets versions add`)
- [ ] 11.8 Write `modules/compute/` Terraform: Cloud Run service for API, Cloud Run service for worker, min/max instances, VPC connector, Cloud SQL sidecar config, environment variable bindings, Secret Manager secret mounts
- [ ] 11.9 Write `modules/tasks/` Terraform: Cloud Tasks queue (`resumai-jobs`), rate limits, retry config
- [ ] 11.10 Write `envs/staging/main.tf` and `envs/prod/main.tf` composing the modules with environment-specific `tfvars`
- [ ] 11.11 Import existing GCP resources (current Cloud Run service, GCS bucket) into Terraform state to avoid recreation
- [ ] 11.12 Run `terraform plan` against staging; confirm no destructive changes on first apply

## 12. CI/CD Decoupling

- [ ] 12.1 Refactor source repo `.github/workflows/ci.yml`: remove all `gcloud run deploy` and `gcloud` deploy commands; retain only lint, test, build, push steps
- [ ] 12.2 Add Workload Identity Federation authentication step to source repo CI (`google-github-actions/auth@v2`) for Artifact Registry push; remove any stored service account JSON keys from GitHub Secrets
- [ ] 12.3 Update Docker build step to tag image as `REGION-docker.pkg.dev/PROJECT/resumai/api:${{ github.sha }}`
- [ ] 12.4 Add final CI step: `workflow_dispatch` to `resumai-infra` repo passing `image_digest` output from the push step (requires a `INFRA_REPO_TOKEN` secret with `workflow` scope on the IaC repo, OR use GitHub App)
- [ ] 12.5 Create `resumai-infra/.github/workflows/cd.yml`: triggers on `workflow_dispatch` (image digest input) and on `push` to `main` within IaC repo
- [ ] 12.6 Add Workload Identity Federation authentication to IaC repo CD workflow for `terraform apply` permissions
- [ ] 12.7 Add `terraform plan` step to IaC repo PR workflow; post plan output as PR comment using `github-script`
- [ ] 12.8 Add `terraform apply -auto-approve` step to IaC repo CD workflow (runs only on `main` merge or `workflow_dispatch`)
- [ ] 12.9 Verify PR builds on source repo do NOT trigger any deployment (review CD workflow trigger conditions)
- [ ] 12.10 Document the CI/CD flow in `resumai-infra/README.md`: trigger sequence, required secrets, rollback procedure

## 13. GCS File Tracking in PostgreSQL

- [ ] 13.1 Add `gcs_files` table to Alembic migration: columns per spec, UNIQUE index on `gcs_path`, FK to `users.id` with cascade delete
- [ ] 13.2 Define `GcsFile` SQLAlchemy ORM model in `backend/app/models/`
- [ ] 13.3 Update `resume_service.py` upload handler: wrap GCS upload and `gcs_files` insert in a single async context — insert DB record with `status='pending'` first, upload to GCS, update `status='active'`; rollback DB record on GCS failure
- [ ] 13.4 Add `gcs_file_id` FK column to `ResumeSession` model (nullable on creation, populated after `gcs_files` insert)
- [ ] 13.5 Implement `GET /api/files/{file_id}/url` — verify ownership, generate 1-hour signed GCS URL
- [ ] 13.6 Implement `DELETE /api/files/{file_id}` — verify ownership, soft-delete DB record (`deleted_at`, `status='deleted'`), delete GCS object
- [ ] 13.7 Implement `GET /api/files/` — list active `gcs_files` records for the authenticated user (paginated)
- [ ] 13.8 Create `backend/app/services/gcs_orphan_scanner.py` — lists GCS bucket objects, queries `gcs_files` for each path, logs unmatched paths, emits `resumai/gcs_orphans_detected` Cloud Monitoring metric
- [ ] 13.9 Add Cloud Scheduler job via Terraform (`modules/tasks/`) to invoke the orphan scanner daily via a Cloud Run Job or HTTP endpoint
- [ ] 13.10 Write pytest tests for upload (success, GCS failure rollback), signed URL (owned, not owned), soft delete (owned, not owned), and orphan scanner (mock GCS listing vs DB)
