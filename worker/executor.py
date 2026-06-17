"""
Worker Executor Interface

Defines the protocol that all runners must implement.
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.jobs.schemas import JobRecord


class JobRunner(Protocol):
    def submit(self, job: "JobRecord") -> None: ...
    def healthcheck(self) -> bool: ...
