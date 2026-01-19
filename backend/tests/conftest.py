"""
Pytest configuration for backend tests
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def client():
    """Create test client for all tests to reuse"""
    app = create_app()
    return TestClient(app)
