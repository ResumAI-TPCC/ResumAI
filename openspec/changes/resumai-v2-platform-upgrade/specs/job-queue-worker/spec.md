## ADDED Requirements

### Requirement: Async job dispatch for long-running operations
The system SHALL dispatch analyze, optimize, and match operations as Cloud Tasks HTTP tasks targeting an internal worker endpoint, returning a `job_id` immediately to the caller.

#### Scenario: Analyze request returns job ID immediately
- **WHEN** `POST /api/v2/resumes/analyze` is called
- **THEN** the endpoint responds within 500 ms with `{ job_id, status_url }` (HTTP 202 Accepted) and enqueues the work to Cloud Tasks

#### Scenario: Worker processes the job
- **WHEN** Cloud Tasks delivers the task to `POST /internal/jobs/{job_id}/process`
- **THEN** the worker executes the LangChain chain, stores the result in `analysis_results`, and updates `job_status` to `completed`

### Requirement: Job status polling endpoint
The system SHALL provide `GET /api/jobs/{job_id}` returning the current status and result of a job.

#### Scenario: Pending job returns status only
- **WHEN** `GET /api/jobs/{job_id}` is called and the job is still queued or running
- **THEN** the response is `{ job_id, status: "pending" | "processing" }` with HTTP 200

#### Scenario: Completed job returns result
- **WHEN** `GET /api/jobs/{job_id}` is called and the job is done
- **THEN** the response is `{ job_id, status: "completed", result: { ... } }` with the full payload

#### Scenario: Failed job returns error
- **WHEN** `GET /api/jobs/{job_id}` is called and the job failed
- **THEN** the response is `{ job_id, status: "failed", error: { code, message } }`

### Requirement: Idempotent job handlers
Worker handlers SHALL be idempotent: re-delivering the same Cloud Tasks task SHALL NOT create duplicate database records.

#### Scenario: Duplicate task delivery is handled
- **WHEN** Cloud Tasks delivers the same `job_id` task twice (retry after timeout)
- **THEN** the second delivery detects the existing `job_status = completed` record and returns HTTP 200 without re-running the chain

### Requirement: Job ownership enforced
`GET /api/jobs/{job_id}` SHALL return HTTP 403 if the authenticated user does not own the job.

#### Scenario: Unauthorized job access blocked
- **WHEN** user A calls `GET /api/jobs/{job_id}` for a job belonging to user B
- **THEN** the response is HTTP 403 `{ code: "FORBIDDEN" }`

### Requirement: Frontend polls for job completion
The frontend SHALL poll `GET /api/jobs/{job_id}` every 2 seconds until `status` is `completed` or `failed`, with a maximum of 60 polls (2-minute timeout).

#### Scenario: UI shows progress indicator during poll
- **WHEN** a job is dispatched and polling begins
- **THEN** the UI displays a progress spinner with elapsed time

#### Scenario: Poll timeout surfaces error
- **WHEN** 60 polls complete without a terminal status
- **THEN** the UI shows a timeout error and offers a "Retry" button
