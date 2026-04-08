## ADDED Requirements

### Requirement: Every GCS object has a corresponding `gcs_files` database record
The system SHALL maintain a `gcs_files` table in PostgreSQL that records every object written to GCS. A GCS object without a `gcs_files` row is considered an orphan and SHALL be flagged for deletion.

#### Scenario: Upload creates DB record before GCS write
- **WHEN** a user uploads a resume file
- **THEN** the upload handler inserts a `gcs_files` row (with `status = 'pending'`) inside a database transaction BEFORE streaming the file to GCS; if the GCS write fails the transaction is rolled back and no orphan is created

#### Scenario: GCS write success updates record status
- **WHEN** the GCS upload completes successfully
- **THEN** the `gcs_files` row status is updated to `'active'` and `gcs_path` is confirmed as the canonical object path

#### Scenario: Duplicate upload path rejected
- **WHEN** a `gcs_path` value already exists in `gcs_files`
- **THEN** the database UNIQUE constraint on `gcs_path` raises an error and the upload is rejected with HTTP 409

### Requirement: `gcs_files` schema
The `gcs_files` table SHALL have the following columns:

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users.id) | NOT NULL; cascade delete |
| `gcs_path` | TEXT (UNIQUE) | Full object path: `{prefix}/{session_id}/{filename}` |
| `original_filename` | TEXT | |
| `content_type` | TEXT | MIME type |
| `file_size_bytes` | BIGINT | |
| `status` | TEXT | `pending`, `active`, `deleted` |
| `uploaded_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | Nullable; NULL = no expiry |
| `deleted_at` | TIMESTAMPTZ | Nullable; soft-delete timestamp |

#### Scenario: Schema applied via Alembic migration
- **WHEN** `alembic upgrade head` is run
- **THEN** the `gcs_files` table with all columns and the UNIQUE index on `gcs_path` is created

### Requirement: File ownership enforced on all GCS file operations
Any API endpoint that reads, deletes, or generates a signed URL for a GCS file SHALL verify that the requesting user owns the `gcs_files` record.

#### Scenario: Owner can retrieve signed URL for their file
- **WHEN** the owning user calls `GET /api/files/{file_id}/url`
- **THEN** a short-lived (1-hour) signed GCS URL is returned

#### Scenario: Non-owner access rejected
- **WHEN** a different authenticated user calls `GET /api/files/{file_id}/url` for a file they do not own
- **THEN** the endpoint returns HTTP 403 `{ code: "FORBIDDEN" }`

### Requirement: Soft delete of GCS files
`DELETE /api/files/{file_id}` SHALL soft-delete the `gcs_files` record (set `deleted_at`, update `status = 'deleted'`) AND delete the actual GCS object.

#### Scenario: Deleted file is inaccessible via API
- **WHEN** a file is soft-deleted
- **THEN** subsequent calls to `GET /api/files/{file_id}/url` return HTTP 404

#### Scenario: GCS object removed on soft delete
- **WHEN** `DELETE /api/files/{file_id}` is called
- **THEN** the GCS object at `gcs_path` is deleted from the bucket within the same request

### Requirement: Orphan detection job
A scheduled job SHALL run daily to identify GCS objects that have no corresponding `gcs_files` record and log them for review.

#### Scenario: Orphan GCS objects are detected and logged
- **WHEN** the orphan-scan job runs
- **THEN** it lists all objects in the GCS bucket, queries `gcs_files` for their `gcs_path`, logs any unmatched objects with their paths and sizes, and emits a Cloud Monitoring metric `resumai/gcs_orphans_detected`

#### Scenario: Orphan scan does not auto-delete without review
- **WHEN** orphans are found
- **THEN** no automatic deletion occurs; deletion requires manual review (safety guardrail)

### Requirement: GCS bucket lifecycle rules aligned with `expires_at`
The GCS bucket SHALL have a lifecycle rule deleting objects older than `SESSION_EXPIRY_HOURS + 1 hour` as a safety net for objects whose DB record was already soft-deleted or whose `expires_at` has passed.

#### Scenario: Expired objects cleaned up by lifecycle rule
- **WHEN** a GCS object's age exceeds the configured expiry TTL
- **THEN** GCS automatically deletes it regardless of DB state; the orphan scan will not flag it as an orphan since it is gone
