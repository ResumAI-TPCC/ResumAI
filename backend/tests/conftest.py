"""
Pytest configuration for backend tests
"""

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def client():
    """Create test client for all tests to reuse"""
    app = create_app()
    return TestClient(app)
