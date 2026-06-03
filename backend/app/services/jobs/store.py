"""
In-memory job store for the Phase 1 async path.
"""

from __future__ import annotations

from dataclasses import replace
from threading import Lock

from .schemas import JobPayload, JobRecord, JobStatus, new_job_id, utc_now_iso


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, payload: JobPayload) -> JobRecord:
        with self._lock:
            now = utc_now_iso()
            record = JobRecord(
                job_id=new_job_id(),
                payload=payload,
                status=JobStatus.ACCEPTED,
                created_at=now,
                updated_at=now,
            )
            self._jobs[record.job_id] = record
            return record

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            updated = replace(record, status=status, updated_at=utc_now_iso())
            self._jobs[job_id] = updated
            return updated

    def complete(self, job_id: str, result: dict) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            updated = replace(
                record,
                status=JobStatus.COMPLETED,
                updated_at=utc_now_iso(),
                result=result,
                error=None,
            )
            self._jobs[job_id] = updated
            return updated

    def fail(self, job_id: str, error: str) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            updated = replace(
                record,
                status=JobStatus.FAILED,
                updated_at=utc_now_iso(),
                error=error,
            )
            self._jobs[job_id] = updated
            return updated
