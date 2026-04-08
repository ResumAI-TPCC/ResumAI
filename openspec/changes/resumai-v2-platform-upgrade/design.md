## Context

ResumAI v1 is a stateless, session-based resume tool running on GCP Cloud Run (backend) and Firebase Hosting (frontend). Every request is self-contained: files live in GCS for 24 h and there is no persistent identity or history. The LLM layer calls Gemini directly through a hand-rolled HTTP provider. All secrets are stored in GitHub Secrets / `.env` files.

V2 transforms this into a authenticated, persistent platform with a structured AI pipeline, semantic search, async job processing, and full observability — while keeping the GCP-native deployment model.

## Goals / Non-Goals

**Goals:**
- Add Google OAuth 2.0 identity with persistent user profiles and resume/analysis history (PostgreSQL on Cloud SQL)
- Replace direct Gemini calls with a LangChain pipeline enabling structured chains, tool use, and model-agnostic swap
- Add pgvector-backed semantic JD matching as an upgrade to keyword matching
- Decouple long-running jobs (analyze, optimize, match) from HTTP via async job queue (Cloud Tasks)
- Integrate LangSmith for LLM observability and cost tracking
- Enable visual workflow prototyping via Langflow export → LangChain import
- Redesign frontend with a marketing landing page and refreshed analysis UX
- Migrate all secrets to GCP Secret Manager; remove reliance on GitHub Secrets and `.env` in production

**Non-Goals:**
- Multi-tenancy / team workspaces (V3+)
- Real-time job board integrations or automated apply features
- Mobile native apps
- Self-hosted LLM inference
- Billing / subscription management (V3+)

## Decisions

### D1 — Keep FastAPI; integrate LangChain as a service layer, not a framework replacement
LangChain will replace the content of `llm/gemini_provider.py` and orchestrate chains, but FastAPI stays as the HTTP layer. Reason: LangChain as a full "server" (LangServe) adds complexity and change surface; the existing three-layer architecture (routes → services → providers) already maps cleanly to a LangChain service module.

*Alternatives considered*: LangServe — rejected (forces route structure); raw Gemini SDK only — rejected (no structured chain/tool support).

### D2 — PostgreSQL on Cloud SQL (not Firestore or Spanner)
Cloud SQL with pgvector extension satisfies both relational history storage and vector similarity search in one managed service. It avoids dual-database complexity.

*Alternatives considered*: Firestore (no vector search without Vertex AI Match); AlloyDB (GA but pricier, overkill at this stage); Pinecone + Firestore (dual DB, more ops overhead).

### D3 — Async job processing via Cloud Tasks (not Celery + Redis)
Cloud Tasks is fully managed, GCP-native, and requires no additional infrastructure. Long-running jobs (analyze: ~10 s, optimize: ~20 s) will be dispatched as Cloud Tasks HTTP targets hitting internal Cloud Run worker endpoints. Clients poll a `/jobs/{job_id}` status endpoint.

*Alternatives considered*: Celery + Redis (more control, but requires Redis instance and worker fleet management); Pub/Sub (better for fan-out; overkill for per-job dispatch).

### D4 — JWT session tokens stored in HTTP-only cookies (not localStorage)
After OAuth callback, the backend issues a short-lived JWT (15 min) + refresh token stored as HTTP-only `SameSite=Strict` cookies. This prevents XSS token theft.

*Alternatives considered*: localStorage (XSS risk); Firebase Auth client SDK (couples frontend to Firebase; backend would still need to verify tokens separately).

### D5 — LangSmith integrated at the LangChain service layer; Langflow used offline for design only
LangSmith tracing is enabled via environment variable (`LANGCHAIN_TRACING_V2=true`) — zero code change needed once LangChain is wired. Langflow is used as a design/prototyping tool; flows are exported and translated to LangChain LCEL code — Langflow does **not** run in production.

*Alternatives considered*: Running Langflow as a runtime server — rejected (adds deployment complexity, not production-hardened for high traffic).

### D6 — GCP Secret Manager accessed at startup, cached in `get_settings()`
The existing `get_settings()` singleton (`@lru_cache`) is extended: if running in GCP (detected by `GOOGLE_CLOUD_PROJECT` env var), secrets are fetched from Secret Manager and injected into the settings object. Local dev retains `.env` fallback.

*Alternatives considered*: Fetching secrets per-request (latency cost, rate limit risk); Berglas sidecar (adds infra complexity).

### D7 — Database migrations via Alembic; SQLAlchemy ORM for models
Standard Python ORM stack. Alembic migration scripts are versioned in `backend/migrations/`. CI runs `alembic upgrade head` before deploying.

### D8 — pgvector embeddings generated via `text-embedding-004` (Google) through LangChain embeddings interface
Keeps all AI within Google's ecosystem, shares the same API key, and avoids OpenAI dependency. Embeddings stored in `vector(768)` columns; cosine similarity via `<=>` operator.

### D9 — Terraform in a dedicated `resumai-infra` repository; GCS backend for remote state
Infrastructure is separated from application code so that infrastructure changes (scaling config, IAM bindings, environment variables, new Cloud Run revisions) can be reviewed and applied independently without touching the source repo. Terraform was chosen over Pulumi (Python familiarity would fit, but Terraform has broader GCP provider coverage and more community modules) and over direct gcloud CLI (no state management, no drift detection).

The `resumai-infra` repo contains modules for: `compute/` (Cloud Run services + traffic splits), `database/` (Cloud SQL, Auth Proxy config), `storage/` (GCS bucket + lifecycle rules), `secrets/` (Secret Manager secret declarations), `iam/` (service accounts, Workload Identity Federation), `tasks/` (Cloud Tasks queue).

*Alternatives considered*: Pulumi (good Python support, but Terraform GCP provider is more mature); Cloud Deployment Manager (GCP-native but limited modularity); keeping infra in same repo (complicates CI triggering and access control).

### D10 — CI in source repo; CD in IaC repo (strict pipeline separation)
The source repo (`ResumAI`) CI workflow is responsible only for: lint → test → Docker build → push image to Artifact Registry (tagged by git SHA). It emits a `workflow_dispatch` event (or writes to a shared signal) containing the image digest. The IaC repo picks this up, updates the Cloud Run service Terraform variable for the new image digest, and runs `terraform apply`. This means:
- No application secrets live in the source repo's GitHub Actions environment — only GCP auth credentials for Artifact Registry push.
- All environment variable injection, scaling configuration, and service account binding is managed in the IaC repo.
- Rollback is a Terraform revert to the previous image digest, auditable in git history.

*Alternatives considered*: Monorepo CI/CD (simpler but credentials sprawl, IaC changes trigger full app builds); CD in source repo with gcloud CLI (no state tracking, hard to roll back).

### D11 — Dedicated `gcs_files` table as the authoritative GCS object registry
Every object written to GCS — resumes, optimized PDFs, any future file type — MUST have a corresponding `gcs_files` row linked to `user_id`. This table is the source of truth for:
- Per-user file listing and deletion
- Expiry management (`expires_at` field drives both GCS lifecycle rules and soft-delete queries)
- Orphan detection (any GCS object without a DB record is an orphan)

The upload handler writes the `gcs_files` record **before** streaming to GCS; if the GCS upload fails, the DB record is rolled back. This prevents silent data loss while ensuring no orphan GCS objects.

The existing `resume_sessions.gcs_path` column is retained as a direct FK to `gcs_files.gcs_path` (denormalised for query convenience).

*Alternatives considered*: GCS Object Notifications → Pub/Sub → DB insert (event-driven, but eventual consistency creates a race window); relying on GCS metadata tags alone (no DB query capability).

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Cloud SQL cold-start latency on Cloud Run | Use Cloud SQL Auth Proxy as a sidecar; maintain min-instances=1 on the API service |
| LangChain version churn (breaking changes between minor versions) | Pin to a minor version; add integration tests for the full chain |
| Cloud Tasks retry on worker failure can duplicate DB writes | Make all job handlers idempotent using `job_id` as an upsert key |
| pgvector query performance at scale | Index with `ivfflat`; revisit with `hnsw` if p95 latency > 200 ms |
| OAuth CSRF during callback | Validate `state` parameter; PKCE flow enforced |
| Secret Manager quota (6000 access/min project-wide) | Cache secrets in `get_settings()` singleton; never fetch per-request |
| Langflow-exported flows may diverge from production chains | Treat Langflow as a design artifact only; production code is hand-written LCEL |
| Breaking change to analyze/match/optimize response shape | Version the API (`/api/v2/resumes/`); keep `/api/resumes/` (v1) alive for one release cycle |
| Terraform state drift if someone applies gcloud CLI changes outside IaC repo | Enforce IaC-only policy; run `terraform plan` in CI and block merges with drift |
| Source repo CI pushes image but IaC CD fails — orphan image in Artifact Registry | Tag images with git SHA; IaC CD workflow retries on failure; stale images cleaned by AR retention policy |
| GCS upload succeeds but `gcs_files` DB write fails — orphaned GCS object | Write DB record first; rollback DB on GCS failure; scheduled orphan-scan job compares GCS bucket listing vs DB |

## Migration Plan

### Phase 0 — Infrastructure prep (no user impact)
1. **Create `resumai-infra` repository** with Terraform module structure; configure GCS remote state bucket
2. Write Terraform modules for existing resources first (Cloud Run, GCS bucket, IAM) to bring current infra under IaC control
3. Provision Cloud SQL (postgres 15 + pgvector) via Terraform
4. Create Secret Manager secrets for all credentials; configure Workload Identity Federation for GitHub Actions in both repos
5. Add Cloud Tasks queue via Terraform; create internal worker Cloud Run service definition
6. Update source repo GitHub Actions CI to: lint → test → build → push image → dispatch to IaC repo (remove all CD steps)

### Phase 1 — Auth + DB foundation
1. Deploy Alembic schema (`users`, `sessions`, `resume_history`, `job_results` tables)
2. Implement Google OAuth flow (backend callback + JWT issuance); add auth middleware
3. Update frontend: landing page, login button, protected routes, job history view

### Phase 2 — LangChain pipeline
1. Implement LangChain service replacing `gemini_provider.py`; keep `BaseLLMProvider` interface intact to avoid route changes
2. Wire LangSmith — enable tracing in staging first; validate cost impact

### Phase 3 — Async jobs + pgvector
1. Implement job dispatcher (Cloud Tasks) and worker handlers
2. Update frontend to poll `/jobs/{job_id}`
3. Generate and store embeddings; implement pgvector semantic match endpoint

### Phase 4 — V2 stabilisation
1. Remove v1 endpoints after one release cycle
2. Load test async pipeline; tune Cloud SQL connection pool

### Rollback
- Phases 0–1: Cloud SQL and Secret Manager are additive; rollback by re-enabling `.env` secrets and removing auth middleware
- Phase 2: `BaseLLMProvider` interface unchanged; revert to `gemini_provider.py` by changing factory registration
- Phase 3: Job queue is a new endpoint; v1 sync endpoints remain until Phase 4

## Open Questions

1. **Embedding storage vs Vertex AI Vector Search** — At what user scale does Cloud SQL + pgvector need to migrate to Vertex AI Vector Search? Define a threshold (e.g., >1M embeddings).
2. **Langflow hosting** — Should Langflow run as an internal dev tool (local Docker only) or a shared staging instance for the team?
3. **Refresh token rotation** — Use rotating refresh tokens (revoke on reuse) or simple sliding-window expiry? Depends on security requirements.
4. **Rate limiting strategy** — Cloud Tasks rate-limits job submission; do we also need per-user rate limits at the API level before auth is matured?
5. **Legacy session migration** — Anonymous (UUID) sessions created before V2 cannot be associated with users. Confirm: discard on V2 launch or offer a one-time claim flow?
6. **IaC monorepo vs polyrepo** — Should `resumai-infra` be an entirely separate repository or a subdirectory of this repo with separate GitHub Actions triggers? Separate repo preferred (independent access control, cleaner CI/CD separation) but needs cross-repo workflow dispatch configuration.
7. **GCS orphan scan frequency** — How often should the orphan-detection job run (daily cron vs triggered after each failed upload)? Daily Cloud Scheduler job recommended initially.
