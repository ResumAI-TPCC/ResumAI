## ADDED Requirements

### Requirement: All secrets retrieved from GCP Secret Manager at startup
The system SHALL read all production credentials from GCP Secret Manager using `google-cloud-secret-manager`, injected into the `Settings` object via `get_settings()`. Local development retains `.env` file fallback.

#### Scenario: Secrets loaded from Secret Manager in Cloud Run
- **WHEN** the backend starts in Cloud Run with `GOOGLE_CLOUD_PROJECT` set and the service account has `roles/secretmanager.secretAccessor`
- **THEN** `GEMINI_API_KEY`, `DATABASE_URL`, `GCS_BUCKET_NAME`, and `LANGCHAIN_API_KEY` are resolved from Secret Manager without any `.env` file present

#### Scenario: Local dev falls back to .env
- **WHEN** `GOOGLE_CLOUD_PROJECT` is absent (local environment)
- **THEN** `get_settings()` reads from `.env` as before; no Secret Manager call is made

#### Scenario: Missing secret causes fast-fail on startup
- **WHEN** a required secret does not exist in Secret Manager (or the service account lacks access)
- **THEN** the application raises a `ConfigurationError` at startup with a clear message identifying the missing secret name

### Requirement: GitHub Actions does not hold application secrets
CI/CD pipelines SHALL only hold `GOOGLE_APPLICATION_CREDENTIALS` (or Workload Identity Federation configuration). All application secrets SHALL be sourced from Secret Manager at runtime.

#### Scenario: GitHub Actions deploy workflow contains no app secrets
- **WHEN** the deploy workflow YAML is inspected
- **THEN** no `GEMINI_API_KEY`, `DATABASE_URL`, or other application secret appears as a GitHub Actions secret or env var — only GCP auth credentials are present

### Requirement: Secret versioning and rotation supported
The Secret Manager integration SHALL always access the `latest` version of each secret by default, enabling zero-downtime secret rotation.

#### Scenario: Secret rotated without redeployment
- **WHEN** a new secret version is added in Secret Manager (e.g., rotated `GEMINI_API_KEY`)
- **THEN** the next application startup picks up the new version automatically; the running instance continues with the cached value until restarted
