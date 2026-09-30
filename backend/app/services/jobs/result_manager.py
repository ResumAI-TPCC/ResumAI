"""
Result Manager (RA-82)

In-memory store for async job results.

Design decisions:
- Plain dict keyed by job_id — no external dependencies.
- Lazy TTL expiry: checked on read, not via a background sweep.
  Keeps implementation minimal; acceptable for MVP traffic levels.
- If a result is expired or never existed, get() returns None and
  the caller is responsible for raising HTTP 404.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResultManager:
    """
    Thread-safe (asyncio-safe) in-memory job result store.

    Each entry shape:
    {
        "job_id":       str,
        "job_type":     str,          # "analyze" | "match" | "optimize"
        "status":       str,          # "pending" | "processing" | "completed" | "failed"
        "result":       Any | None,   # populated on completion
        "error":        str | None,   # populated on failure
        "created_at":   datetime,
        "completed_at": datetime | None,
    }
    """

    def __init__(self, ttl_seconds: int | None = None):
        self._store: dict[str, dict] = {}
        self._ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.RESULT_TTL_SECONDS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, job_id: str, job_type: str) -> None:
        """Register a new job with status 'pending'."""
        self._store[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "completed_at": None,
        }
        logger.debug(f"Job created: {job_id} ({job_type})")

    def set_processing(self, job_id: str) -> None:
        """Mark a job as currently being processed by a worker."""
        entry = self._store.get(job_id)
        if entry:
            entry["status"] = "processing"

    def set_completed(self, job_id: str, result: Any) -> None:
        """Store the successful result and mark job as completed."""
        entry = self._store.get(job_id)
        if entry:
            entry["status"] = "completed"
            entry["result"] = result
            entry["completed_at"] = datetime.now(timezone.utc)
            logger.debug(f"Job completed: {job_id}")

    def set_failed(self, job_id: str, error: str) -> None:
        """Store the error message and mark job as failed."""
        entry = self._store.get(job_id)
        if entry:
            entry["status"] = "failed"
            entry["error"] = error
            entry["completed_at"] = datetime.now(timezone.utc)
            logger.warning(f"Job failed: {job_id} — {error}")

    def get(self, job_id: str) -> Optional[dict]:
        """
        Retrieve a job entry.

        Returns None (caller should 404) if:
        - job_id does not exist
        - entry has exceeded TTL (lazy expiry: entry is deleted on access)
        """
        entry = self._store.get(job_id)
        if entry is None:
            return None

        age_seconds = (
            datetime.now(timezone.utc) - entry["created_at"]
        ).total_seconds()

        if age_seconds > self._ttl_seconds:
            del self._store[job_id]
            logger.info(f"Job expired and removed: {job_id} (age={age_seconds:.0f}s)")
            return None

        return entry

    def size(self) -> int:
        """Return the total number of entries currently held in memory."""
        return len(self._store)


@lru_cache
def get_result_manager() -> ResultManager:
    """Return the singleton ResultManager instance."""
    return ResultManager()
