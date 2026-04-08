## MODIFIED Requirements

### Requirement: Resume analysis returns async job reference
The analyze endpoint SHALL return an async job reference instead of a synchronous result. The HTTP response MUST be HTTP 202 with `{ job_id, status_url }`.

- **WHEN** `POST /api/v2/resumes/analyze` is called with a valid `session_id`
- **THEN** the server responds within 500 ms with HTTP 202 `{ code: "ACCEPTED", status: "success", data: { job_id: "<uuid>", status_url: "/api/jobs/<uuid>" } }`

#### Scenario: Analysis job enqueued successfully
- **WHEN** the authenticated user calls `POST /api/v2/resumes/analyze` with a valid `session_id`
- **THEN** the endpoint returns HTTP 202 within 500 ms and a Cloud Tasks task is enqueued

#### Scenario: Unknown session returns 404
- **WHEN** the `session_id` does not exist in the database or does not belong to the authenticated user
- **THEN** the endpoint returns HTTP 404 `{ code: "SESSION_NOT_FOUND" }`

### Requirement: Job-description match returns async job reference
The match endpoint SHALL return an async job reference.

#### Scenario: Match job enqueued successfully
- **WHEN** the authenticated user calls `POST /api/v2/resumes/match` with `session_id` and `job_description`
- **THEN** the endpoint returns HTTP 202 with `{ job_id, status_url }`

### Requirement: Resume optimization returns async job reference
The optimize endpoint SHALL return an async job reference. The PDF download SHALL be available via the completed job result URL.

#### Scenario: Optimize job enqueued successfully
- **WHEN** the authenticated user calls `POST /api/v2/resumes/optimize`
- **THEN** the endpoint returns HTTP 202 with `{ job_id, status_url }`

#### Scenario: Completed optimize job result contains download URL
- **WHEN** `GET /api/jobs/{job_id}` returns `status: "completed"` for an optimize job
- **THEN** the `result` field contains `{ pdf_url: "<signed GCS URL>" }` valid for 1 hour

## REMOVED Requirements

### Requirement: Synchronous v1 analyze/match/optimize response
**Reason**: Replaced by the async job-queue pattern in V2. Synchronous responses with full LLM payloads cause HTTP timeouts under load and do not support progress indication.
**Migration**: Use `POST /api/v2/resumes/analyze` (match, optimize) and poll `GET /api/jobs/{job_id}`. V1 endpoints (`/api/resumes/analyze`, `/api/resumes/match`, `/api/resumes/optimize`) will remain available for one release cycle and then be removed.
