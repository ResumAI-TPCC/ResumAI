"""
Job manager for Phase 1 async orchestration.
"""

from __future__ import annotations

from typing import Protocol

from .schemas import JobPayload, JobReceipt, JobStatus
from .store import InMemoryJobStore


class JobRunner(Protocol):
    def submit(self, job_record) -> None: ...


class JobRunnerUnavailableError(RuntimeError):
    """Raised when the configured runner cannot accept a job."""


class JobManager:
    def __init__(self, store: InMemoryJobStore, runner: JobRunner) -> None:
        self._store = store
        self._runner = runner

    def submit_job(self, payload: JobPayload) -> JobReceipt:
        record = self._store.create(payload)
        queued_record = self._store.update_status(record.job_id, JobStatus.QUEUED)

        try:
            self._runner.submit(queued_record)
        except Exception as exc:
            self._store.update_status(record.job_id, JobStatus.REJECTED)
            raise JobRunnerUnavailableError(
                "Task service is temporarily unavailable."
            ) from exc

        return JobReceipt(
            job_id=queued_record.job_id,
            job_status=queued_record.status.value,
        )

    def get_job(self, job_id: str):
        return self._store.get(job_id)
