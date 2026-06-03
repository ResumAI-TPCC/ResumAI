"""
Schemas for the Phase 1 async job model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
import uuid


class JobStatus(StrEnum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(slots=True)
class JobPayload:
    task_type: str
    session_id: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobRecord:
    job_id: str
    payload: JobPayload
    status: JobStatus
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass(slots=True)
class JobReceipt:
    job_id: str
    job_status: str
    deduplicated: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_job_id() -> str:
    return str(uuid.uuid4())
