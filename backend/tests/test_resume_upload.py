from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_resume_upload_success_pdf():
    app = create_app()
    client = TestClient(app)

    files = {"file": ("test.pdf", b"%PDF-1.4\nfake\n", "application/pdf")}
    r = client.post(f"{settings.api_prefix}/resume/", files=files)

    assert r.status_code == 200, r.text
    data = r.json()
    assert "file_id" in data
    assert data["filename"] == "test.pdf"
    assert "storage_path" in data


def test_resume_upload_reject_txt():
    app = create_app()
    client = TestClient(app)

    files = {"file": ("test.txt", b"hello", "text/plain")}
    r = client.post(f"{settings.api_prefix}/resume/", files=files)

    assert r.status_code == 400, r.text