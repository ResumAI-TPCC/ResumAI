import os
import sys
from pathlib import Path

# Inject mock environment variables before app code initializes settings
# This ensures Pydantic validation passes even if variables are missing in the environment
os.environ.setdefault("GCP_PROJECT_ID", "mock-project-id")
os.environ.setdefault("GCS_BUCKET_NAME", "mock-bucket-name")

# Ensure backend/app is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
