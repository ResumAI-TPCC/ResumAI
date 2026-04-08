## ADDED Requirements

### Requirement: PostgreSQL schema for user data
The system SHALL provision a PostgreSQL 15 database on Cloud SQL with the following tables: `users`, `refresh_tokens`, `resume_sessions`, `analysis_results`, `match_results`.

#### Scenario: Schema is applied via Alembic on deployment
- **WHEN** the backend container starts in a new environment
- **THEN** running `alembic upgrade head` applies all pending migrations without data loss on subsequent runs (idempotent)

#### Scenario: User table uniqueness
- **WHEN** two users with the same `google_sub` attempt to be inserted
- **THEN** the database enforces a UNIQUE constraint on `google_sub` and the upsert updates the existing row

### Requirement: Resume session history
The system SHALL persist every uploaded resume as a `resume_sessions` record linked to the authenticated user.

#### Scenario: Upload creates history record
- **WHEN** a user uploads a resume via `POST /api/resumes/`
- **THEN** a `resume_sessions` row is created with `user_id`, `gcs_path`, `original_filename`, `uploaded_at`, and `expires_at`

#### Scenario: History is scoped to the authenticated user
- **WHEN** `GET /api/resumes/history` is called
- **THEN** only `resume_sessions` rows belonging to the requesting `user_id` are returned, ordered by `uploaded_at` DESC

### Requirement: Analysis and match result persistence
The system SHALL store the output of every analyze, optimize, and match job in the database linked to the resume session.

#### Scenario: Analysis result stored after completion
- **WHEN** an analysis job completes successfully
- **THEN** an `analysis_results` row is upserted with `job_id`, `resume_session_id`, `suggestions` (JSONB), and `completed_at`

#### Scenario: Retrieve past analysis
- **WHEN** `GET /api/resumes/{session_id}/analysis` is called by the owning user
- **THEN** the most recent `analysis_results` row for that session is returned

### Requirement: Cloud SQL Auth Proxy connectivity
The system SHALL connect to Cloud SQL using the Cloud SQL Auth Proxy (Unix socket in Cloud Run) rather than public IP.

#### Scenario: Backend connects via Unix socket on Cloud Run
- **WHEN** the backend service starts in Cloud Run with the Cloud SQL Auth Proxy sidecar
- **THEN** SQLAlchemy connects via `postgresql+asyncpg:///...?host=/cloudsql/<instance>` without exposing the DB to the public internet

#### Scenario: Local development falls back to TCP
- **WHEN** the `CLOUD_SQL_CONNECTION_NAME` env var is absent
- **THEN** SQLAlchemy connects via `DATABASE_URL` directly (TCP, local Postgres or proxy on 5432)
