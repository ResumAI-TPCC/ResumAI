"""
Development server startup script
"""

import sys
from pathlib import Path

# Add repo root and backend/ to sys.path so both `app.*` and `worker.*` resolve.
_repo_root = Path(__file__).resolve().parent.parent
_backend = Path(__file__).resolve().parent
for _p in (_repo_root, _backend):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload for development
    )
