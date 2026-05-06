"""
Job Store - Redis-based Job State Management

Manages job state and results in Redis for the async task queue.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStore:
    """
    Redis-based job store for managing task state and results.
    
    Job data structure in Redis:
    {
        "job_id": "uuid",
        "status": "queued|processing|completed|failed",
        "task_type": "analyze|match|optimize",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "result": {...} | null,
        "error": "error message" | null
    }
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None
        self._expiry_seconds = settings.JOB_RESULT_EXPIRY_HOURS * 3600
    
    @property
    def client(self) -> redis.Redis:
        """Lazy Redis client initialization"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _job_key(self, job_id: str) -> str:
        """Generate Redis key for job"""
        return f"job:{job_id}"
    
    def create_job(self, job_id: str, task_type: str) -> dict:
        """
        Create a new job record.
        
        Args:
            job_id: Unique job identifier
            task_type: Type of task (analyze, match, optimize)
            
        Returns:
            Job data dictionary
        """
        now = datetime.now(timezone.utc).isoformat()
        job_data = {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "task_type": task_type,
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
        }
        
        key = self._job_key(job_id)
        self.client.setex(
            key,
            self._expiry_seconds,
            json.dumps(job_data)
        )
        
        logger.info(f"Created job {job_id} with status {JobStatus.QUEUED.value}")
        return job_data
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """
        Get job data by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data dictionary or None if not found
        """
        key = self._job_key(job_id)
        data = self.client.get(key)
        
        if data is None:
            return None
        
        return json.loads(data)
    
    def update_status(self, job_id: str, status: JobStatus) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            
        Returns:
            True if updated, False if job not found
        """
        job_data = self.get_job(job_id)
        if job_data is None:
            return False
        
        job_data["status"] = status.value
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        key = self._job_key(job_id)
        ttl = self.client.ttl(key)
        
        if ttl > 0:
            self.client.setex(key, ttl, json.dumps(job_data))
        else:
            self.client.setex(key, self._expiry_seconds, json.dumps(job_data))
        
        logger.info(f"Updated job {job_id} status to {status.value}")
        return True
    
    def set_result(self, job_id: str, result: Any) -> bool:
        """
        Set job result and mark as completed.
        
        Args:
            job_id: Job identifier
            result: Task result data
            
        Returns:
            True if set, False if job not found
        """
        job_data = self.get_job(job_id)
        if job_data is None:
            return False
        
        job_data["status"] = JobStatus.COMPLETED.value
        job_data["result"] = result
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        key = self._job_key(job_id)
        ttl = self.client.ttl(key)
        
        if ttl > 0:
            self.client.setex(key, ttl, json.dumps(job_data))
        else:
            self.client.setex(key, self._expiry_seconds, json.dumps(job_data))
        
        logger.info(f"Set result for job {job_id}")
        return True
    
    def set_error(self, job_id: str, error: str) -> bool:
        """
        Set job error and mark as failed.
        
        Args:
            job_id: Job identifier
            error: Error message
            
        Returns:
            True if set, False if job not found
        """
        job_data = self.get_job(job_id)
        if job_data is None:
            return False
        
        job_data["status"] = JobStatus.FAILED.value
        job_data["error"] = error
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        key = self._job_key(job_id)
        ttl = self.client.ttl(key)
        
        if ttl > 0:
            self.client.setex(key, ttl, json.dumps(job_data))
        else:
            self.client.setex(key, self._expiry_seconds, json.dumps(job_data))
        
        logger.error(f"Job {job_id} failed: {error}")
        return True


# Singleton instance
_job_store: Optional[JobStore] = None


def get_job_store() -> JobStore:
    """Get cached job store instance (singleton pattern)"""
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store
