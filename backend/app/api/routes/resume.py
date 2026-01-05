"""
Resume API Routes
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

router = APIRouter()

# Save uploads under: backend/storage/resumes/<file_id>/<original_filename>
STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage" / "resumes"
ALLOWED_EXTS = {".pdf", ".doc", ".docx"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def _validate_filename(filename: str) -> None:
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTS)}",
        )


# ============================================================================
# Endpoint 1: Upload & Parse Resume (Local mock storage for now)
# ============================================================================
@router.post("/")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload resume file (local mock storage; replace with GCS later)

    Returns:
        dict: {file_id, filename, storage_path}
    """
    _validate_filename(file.filename)

    file_id = str(uuid.uuid4())
    dest_dir = STORAGE_ROOT / file_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / Path(file.filename).name

    # Stream write + size limit
    size = 0
    try:
        with dest_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Max {MAX_SIZE_BYTES} bytes",
                    )
                f.write(chunk)
    finally:
        await file.close()

    # Return path relative to backend/ so future GCS can reuse field name
    storage_path = str(dest_path.relative_to(Path(__file__).resolve().parents[3]))
    return {"file_id": file_id, "filename": file.filename, "storage_path": storage_path}


# ============================================================================
# Endpoint 2: Calculate Match Score
# ============================================================================
@router.post("/match")
async def match_resume():
    """
    Calculate match score between resume and job description

    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume match endpoint", "status": "ok"}


# ============================================================================
# Endpoint 3: Optimize Resume
# ============================================================================
@router.post("/optimize")
async def optimize_resume():
    """
    Optimize resume content

    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume optimize endpoint", "status": "ok"}


# ============================================================================
# Endpoint 4: Analyze & Generate Suggestions
# ============================================================================
@router.post("/analyze")
async def analyze_resume():
    """
    Analyze resume and generate improvement suggestions

    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume analyze endpoint", "status": "ok"}