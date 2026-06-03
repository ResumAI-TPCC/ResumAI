"""
Pytest configuration for backend tests
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set environment variables for testing
os.environ["GCS_BUCKET_NAME"] = "test-bucket"
os.environ["GCP_PROJECT_ID"] = "test-project"

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.auth import get_current_user_claims  # noqa: E402
from app.main import create_app  # noqa: E402
from app.schemas.auth_schema import CurrentUserClaims  # noqa: E402


def fake_current_user() -> CurrentUserClaims:
    """Return a stable authenticated user for route tests."""
    return CurrentUserClaims(
        firebase_uid="test-firebase-uid",
        email="tester@example.com",
        display_name="Test User",
        email_verified=True,
        claims={"uid": "test-firebase-uid"},
    )


@pytest.fixture
def mock_gcs():
    """Mock GCS client for testing"""
    with patch("app.services.storage.gcs_service.get_gcs_client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_client.return_value.bucket.return_value = mock_bucket
        yield mock_client


@pytest.fixture
def client(mock_gcs):
    """Create test client for all tests to reuse"""
    app = create_app()
    app.dependency_overrides[get_current_user_claims] = fake_current_user
    return TestClient(app)
