"""
Tests for Async Queue Module

Tests the Celery + Redis async job processing system.
"""

import pytest
from unittest.mock import patch, MagicMock
import json

from app.services.queue.job_store import JobStore, JobStatus


class TestJobStore:
    """Test cases for JobStore"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    def job_store(self, mock_redis):
        """Create a JobStore with mocked Redis"""
        store = JobStore(redis_url="redis://localhost:6379/0")
        store._client = mock_redis
        return store
    
    def test_create_job(self, job_store, mock_redis):
        """Test creating a new job"""
        job_id = "test-job-123"
        task_type = "analyze"
        
        mock_redis.get.return_value = None
        mock_redis.ttl.return_value = 86400
        
        result = job_store.create_job(job_id, task_type)
        
        assert result["job_id"] == job_id
        assert result["status"] == JobStatus.QUEUED.value
        assert result["task_type"] == task_type
        mock_redis.setex.assert_called_once()
    
    def test_get_job(self, job_store, mock_redis):
        """Test getting a job by ID"""
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "status": "queued",
            "task_type": "analyze",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "result": None,
            "error": None,
        }
        
        mock_redis.get.return_value = json.dumps(job_data)
        
        result = job_store.get_job(job_id)
        
        assert result is not None
        assert result["job_id"] == job_id
        assert result["status"] == "queued"
    
    def test_get_job_not_found(self, job_store, mock_redis):
        """Test getting a non-existent job"""
        mock_redis.get.return_value = None
        
        result = job_store.get_job("non-existent")
        
        assert result is None
    
    def test_update_status(self, job_store, mock_redis):
        """Test updating job status"""
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "status": "queued",
            "task_type": "analyze",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "result": None,
            "error": None,
        }
        
        mock_redis.get.return_value = json.dumps(job_data)
        mock_redis.ttl.return_value = 86400
        
        success = job_store.update_status(job_id, JobStatus.PROCESSING)
        
        assert success is True
        mock_redis.setex.assert_called_once()
    
    def test_set_result(self, job_store, mock_redis):
        """Test setting job result"""
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "status": "processing",
            "task_type": "analyze",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "result": None,
            "error": None,
        }
        result_data = {"suggestions": [{"title": "Test suggestion"}]}
        
        mock_redis.get.return_value = json.dumps(job_data)
        mock_redis.ttl.return_value = 86400
        
        success = job_store.set_result(job_id, result_data)
        
        assert success is True
        mock_redis.setex.assert_called_once()
    
    def test_set_error(self, job_store, mock_redis):
        """Test setting job error"""
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "status": "processing",
            "task_type": "analyze",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "result": None,
            "error": None,
        }
        error_msg = "Test error message"
        
        mock_redis.get.return_value = json.dumps(job_data)
        mock_redis.ttl.return_value = 86400
        
        success = job_store.set_error(job_id, error_msg)
        
        assert success is True
        mock_redis.setex.assert_called_once()


class TestAsyncEndpoints:
    """Test cases for async API endpoints"""
    
    @pytest.mark.asyncio
    async def test_analyze_async_creates_job(self):
        """Test that analyze_async creates a job and returns job_id"""
        from app.api.routes.resumes import analyze_resume_async
        from app.schemas.resume_schema import ResumeAnalyzeRequest
        
        with patch("app.api.routes.resumes.get_resume_content") as mock_get:
            with patch("app.api.routes.resumes.get_job_store") as mock_store:
                with patch("app.api.routes.resumes.analyze_task") as mock_task:
                    mock_get.return_value = "resume content"
                    mock_job_store = MagicMock()
                    mock_job_store.create_job.return_value = {}
                    mock_store.return_value = mock_job_store
                    mock_task.delay = MagicMock()
                    
                    request = ResumeAnalyzeRequest(session_id="test-session")
                    result = await analyze_resume_async(request)
                    
                    assert result.code == 202
                    assert result.status == "accepted"
                    assert result.data.job_id is not None
    
    @pytest.mark.asyncio
    async def test_match_async_creates_job(self):
        """Test that match_async creates a job and returns job_id"""
        from app.api.routes.resumes import match_resume_async
        from app.schemas.resume_schema import ResumeMatchRequest
        
        with patch("app.api.routes.resumes.get_resume_content") as mock_get:
            with patch("app.api.routes.resumes.get_job_store") as mock_store:
                with patch("app.api.routes.resumes.match_task") as mock_task:
                    mock_get.return_value = "resume content"
                    mock_job_store = MagicMock()
                    mock_job_store.create_job.return_value = {}
                    mock_store.return_value = mock_job_store
                    mock_task.delay = MagicMock()
                    
                    request = ResumeMatchRequest(
                        session_id="test-session",
                        job_description="Test JD"
                    )
                    result = await match_resume_async(request)
                    
                    assert result.code == 202
                    assert result.status == "accepted"
                    assert result.data.job_id is not None
    
    @pytest.mark.asyncio
    async def test_optimize_async_creates_job(self):
        """Test that optimize_async creates a job and returns job_id"""
        from app.api.routes.resumes import optimize_resume_async
        from app.schemas.resume_schema import ResumeOptimizeRequest
        
        with patch("app.api.routes.resumes.get_resume_content") as mock_get:
            with patch("app.api.routes.resumes.get_job_store") as mock_store:
                with patch("app.api.routes.resumes.optimize_task") as mock_task:
                    mock_get.return_value = "resume content"
                    mock_job_store = MagicMock()
                    mock_job_store.create_job.return_value = {}
                    mock_store.return_value = mock_job_store
                    mock_task.delay = MagicMock()
                    
                    request = ResumeOptimizeRequest(session_id="test-session")
                    result = await optimize_resume_async(request)
                    
                    assert result.code == 202
                    assert result.status == "accepted"
                    assert result.data.job_id is not None


class TestJobStatusEndpoint:
    """Test cases for job status endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_job_status_success(self):
        """Test getting job status for existing job"""
        from app.api.routes.jobs import get_job_status
        
        with patch("app.api.routes.jobs.get_job_store") as mock_store:
            mock_job_store = MagicMock()
            mock_job_store.get_job.return_value = {
                "job_id": "test-job-123",
                "status": "completed",
                "task_type": "analyze",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z",
                "result": {"suggestions": []},
                "error": None,
            }
            mock_store.return_value = mock_job_store
            
            result = await get_job_status("test-job-123")
            
            assert result.code == 200
            assert result.data.job_id == "test-job-123"
            assert result.data.status == "completed"
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test getting status for non-existent job"""
        from app.api.routes.jobs import get_job_status
        from fastapi import HTTPException
        
        with patch("app.api.routes.jobs.get_job_store") as mock_store:
            mock_job_store = MagicMock()
            mock_job_store.get_job.return_value = None
            mock_store.return_value = mock_job_store
            
            with pytest.raises(HTTPException) as exc_info:
                await get_job_status("non-existent")
            
            assert exc_info.value.status_code == 404
