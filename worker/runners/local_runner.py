"""
LocalBackgroundRunner

Executes jobs in a background thread pool within the backend process.
No Redis or external broker required (Phase 1).

Future: replace with CeleryRunner by implementing the same submit/healthcheck interface.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.services.jobs.schemas import JobRecord, JobStatus
from app.services.jobs.store import InMemoryJobStore

logger = logging.getLogger(__name__)

_TASK_REGISTRY: dict[str, callable] = {}


def _get_task_registry() -> dict[str, callable]:
    """Lazy-load task functions to avoid circular imports at module level."""
    if not _TASK_REGISTRY:
        from worker.tasks.analyze import run_analyze_job
        from worker.tasks.match import run_match_job
        from worker.tasks.optimize import run_optimize_job

        _TASK_REGISTRY["analyze"] = run_analyze_job
        _TASK_REGISTRY["match"] = run_match_job
        _TASK_REGISTRY["optimize"] = run_optimize_job
    return _TASK_REGISTRY


class LocalBackgroundRunner:
    """
    Runs jobs in the backend process using a thread pool.
    Satisfies the JobRunner protocol expected by JobManager.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._store: InMemoryJobStore | None = None

    def set_store(self, store: InMemoryJobStore) -> None:
        """Inject the shared job store so the runner can write back status."""
        self._store = store

    def submit(self, job: JobRecord) -> None:
        """
        Submit a job for background execution.
        Called by JobManager after the job is created.
        """
        self._executor.submit(self._run, job)

    def healthcheck(self) -> bool:
        return not self._executor._shutdown  # noqa: SLF001

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self, job: JobRecord) -> None:
        if self._store is None:
            logger.error("LocalBackgroundRunner has no store; cannot run job %s", job.job_id)
            return

        task_fn = _get_task_registry().get(job.payload.task_type)
        if task_fn is None:
            self._store.fail(job.job_id, f"Unknown task type: {job.payload.task_type}")
            return

        self._store.update_status(job.job_id, JobStatus.PROCESSING)
        try:
            result = task_fn(job.payload)
            self._store.complete(job.job_id, result)
            logger.info("Job %s completed", job.job_id)
        except Exception as exc:
            logger.exception("Job %s failed", job.job_id)
            self._store.fail(job.job_id, str(exc))
