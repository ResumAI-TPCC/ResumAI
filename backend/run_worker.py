#!/usr/bin/env python
"""
Celery Worker Entry Point

Start the Celery worker for processing async resume tasks.

Usage:
    python run_worker.py
    
Or use celery directly:
    celery -A app.services.queue.celery_app worker --loglevel=info
"""

if __name__ == "__main__":
    from app.services.queue.celery_app import celery_app
    
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=4",
        ]
    )
