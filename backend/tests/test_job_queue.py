"""
Unit Tests for RA-82: JobManager and ResultManager

Covers:
- ResultManager: create / get / TTL expiry / set_completed / set_failed / set_processing
- JobManager:    enqueue / queue_depth / QueueFullError / worker lifecycle /
                 worker processes job to completed/failed
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.jobs.result_manager import ResultManager
from app.services.jobs.job_manager import JobManager, QueueFullError


# ===========================================================================
# Helpers
# ===========================================================================

def make_result_manager() -> ResultManager:
    """Return a fresh ResultManager (bypasses lru_cache singleton)."""
    return ResultManager(ttl_seconds=3600)


def make_job_manager(result_manager: ResultManager, max_queue_size: int = 5) -> JobManager:
    """Return a fresh JobManager wired to the given ResultManager."""
    with patch(
        "app.services.jobs.job_manager.get_result_manager",
        return_value=result_manager,
    ):
        return JobManager(max_queue_size=max_queue_size)


# ===========================================================================
# ResultManager Tests
# ===========================================================================

class TestResultManager:
    """Tests for in-memory result store with lazy TTL expiry."""

    def setup_method(self):
        self.rm = make_result_manager()

    # --- create / get ---

    def test_create_stores_pending_entry(self):
        self.rm.create("job-1", "analyze")
        entry = self.rm.get("job-1")

        assert entry is not None
        assert entry["job_id"] == "job-1"
        assert entry["job_type"] == "analyze"
        assert entry["status"] == "pending"
        assert entry["result"] is None
        assert entry["error"] is None

    def test_get_returns_none_for_unknown_id(self):
        assert self.rm.get("nonexistent-id") is None

    # --- set_processing ---

    def test_set_processing_updates_status(self):
        self.rm.create("job-2", "match")
        self.rm.set_processing("job-2")
        assert self.rm.get("job-2")["status"] == "processing"

    # --- set_completed ---

    def test_set_completed_stores_result(self):
        self.rm.create("job-3", "analyze")
        payload = {"suggestions": [{"title": "Add metrics"}]}
        self.rm.set_completed("job-3", payload)

        entry = self.rm.get("job-3")
        assert entry["status"] == "completed"
        assert entry["result"] == payload
        assert entry["completed_at"] is not None

    # --- set_failed ---

    def test_set_failed_stores_error(self):
        self.rm.create("job-4", "optimize")
        self.rm.set_failed("job-4", "Gemini API key invalid")

        entry = self.rm.get("job-4")
        assert entry["status"] == "failed"
        assert entry["error"] == "Gemini API key invalid"
        assert entry["completed_at"] is not None

    # --- TTL expiry (lazy) ---

    def test_expired_entry_returns_none(self):
        """get() removes and returns None when TTL has elapsed."""
        rm = ResultManager(ttl_seconds=1)
        rm.create("job-5", "analyze")

        # Backdate created_at to simulate passage of time
        rm._store["job-5"]["created_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=2)
        )

        assert rm.get("job-5") is None
        assert "job-5" not in rm._store  # lazy delete happened

    def test_non_expired_entry_is_returned(self):
        rm = ResultManager(ttl_seconds=3600)
        rm.create("job-6", "match")
        assert rm.get("job-6") is not None

    # --- size ---

    def test_size_reflects_store_contents(self):
        assert self.rm.size() == 0
        self.rm.create("job-7", "analyze")
        assert self.rm.size() == 1
        self.rm.create("job-8", "match")
        assert self.rm.size() == 2


# ===========================================================================
# JobManager Tests
# ===========================================================================

class TestJobManager:
    """Tests for async job queue — enqueue, depth, capacity, worker lifecycle."""

    def setup_method(self):
        self.rm = make_result_manager()
        self.jm = make_job_manager(self.rm, max_queue_size=5)

    # --- enqueue ---

    def test_enqueue_returns_job_id_string(self):
        job_id = self.jm.enqueue("analyze", MagicMock())
        assert isinstance(job_id, str) and len(job_id) > 0

    def test_enqueue_registers_job_as_pending(self):
        job_id = self.jm.enqueue("analyze", MagicMock())
        entry = self.rm.get(job_id)
        assert entry is not None
        assert entry["status"] == "pending"
        assert entry["job_type"] == "analyze"

    def test_enqueue_accepts_all_job_types(self):
        for job_type in ("analyze", "match", "optimize"):
            job_id = self.jm.enqueue(job_type, MagicMock())
            assert self.rm.get(job_id)["job_type"] == job_type

    # --- queue_depth ---

    def test_queue_depth_starts_at_zero(self):
        assert self.jm.queue_depth == 0

    def test_queue_depth_increases_per_enqueue(self):
        self.jm.enqueue("analyze", MagicMock())
        assert self.jm.queue_depth == 1
        self.jm.enqueue("match", MagicMock())
        assert self.jm.queue_depth == 2

    # --- QueueFullError ---

    def test_enqueue_raises_queue_full_error_at_capacity(self):
        """enqueue() must raise QueueFullError when queue is at max_queue_size."""
        for _ in range(5):
            self.jm.enqueue("analyze", MagicMock())

        assert self.jm.queue_depth == 5

        with pytest.raises(QueueFullError):
            self.jm.enqueue("analyze", MagicMock())

    # --- worker lifecycle ---

    @pytest.mark.asyncio
    async def test_start_creates_running_worker_task(self):
        jm = make_job_manager(self.rm)
        await jm.start()

        assert jm._worker_task is not None
        assert not jm._worker_task.done()

        await jm.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_worker_task(self):
        jm = make_job_manager(self.rm)
        await jm.start()
        await jm.stop()

        assert jm._worker_task.done()

    @pytest.mark.asyncio
    async def test_start_twice_reuses_same_worker_task(self):
        jm = make_job_manager(self.rm)
        await jm.start()
        first_task = jm._worker_task

        await jm.start()  # second call is a no-op
        assert jm._worker_task is first_task

        await jm.stop()

    # --- worker processes jobs ---

    @pytest.mark.asyncio
    async def test_worker_marks_job_completed_on_success(self):
        """Worker should call _execute_job and store result in ResultManager."""
        jm = make_job_manager(self.rm)

        async def fake_execute(job, *_):
            return {"suggestions": [{"title": "Add metrics"}]}

        jm._execute_job = fake_execute
        await jm.start()

        payload = MagicMock()
        payload.session_id = "test-session"
        job_id = jm.enqueue("analyze", payload)

        # Give the event loop a few ticks to let the worker run
        await asyncio.sleep(0.1)
        await jm.stop()

        entry = self.rm.get(job_id)
        assert entry is not None
        assert entry["status"] == "completed"
        assert entry["result"] == {"suggestions": [{"title": "Add metrics"}]}

    @pytest.mark.asyncio
    async def test_worker_marks_job_failed_on_exception(self):
        """Worker should catch exceptions from _execute_job and mark job as failed."""
        jm = make_job_manager(self.rm)

        async def fake_execute_fail(job, *_):
            raise ValueError("LLM error")

        jm._execute_job = fake_execute_fail
        await jm.start()

        payload = MagicMock()
        payload.session_id = "test-session"
        job_id = jm.enqueue("analyze", payload)

        await asyncio.sleep(0.1)
        await jm.stop()

        entry = self.rm.get(job_id)
        assert entry is not None
        assert entry["status"] == "failed"
        assert "LLM error" in entry["error"]
