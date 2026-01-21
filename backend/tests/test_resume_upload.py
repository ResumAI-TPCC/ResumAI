from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.services import resume_service


class FakeBlob:
    def __init__(self) -> None:
        self.data = None
        self.content_type = None
        self.name = None

    def upload_from_string(self, data: bytes, content_type: str | None = None) -> None:
        self.data = data
        self.content_type = content_type


class FakeBucket:
    def __init__(self) -> None:
        self.blobs = {}

    def blob(self, name: str) -> FakeBlob:
        blob = FakeBlob()
        blob.name = name
        self.blobs[name] = blob
        return blob


class FakeClient:
    def __init__(self) -> None:
        self.bucket_name = None
        self.bucket_obj = FakeBucket()

    def bucket(self, name: str) -> FakeBucket:
        self.bucket_name = name
        return self.bucket_obj


def test_resume_upload_success_pdf(monkeypatch):
    app = create_app()
    client = TestClient(app)

    fake_client = FakeClient()
    monkeypatch.setattr(resume_service, "_get_gcs_client", lambda: fake_client)
    monkeypatch.setattr(resume_service.settings, "GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(resume_service.settings, "GCS_OBJECT_PREFIX", "resumes")
    monkeypatch.setattr(resume_service.settings, "GCP_PROJECT_ID", "test-project")

    # Mock _validate_pdf_content to avoid pypdf parsing errors with fake content
    monkeypatch.setattr(resume_service, "_validate_pdf_content", lambda content: None)

    files = {"file": ("test.pdf", b"%PDF-1.4\nfake\n", "application/pdf")}
    r = client.post(f"{settings.API_PREFIX}/resumes/", files=files)

    assert r.status_code == 201, r.text
    res = r.json()
    assert res["status"] == "ok"
    assert "session_id" in res["data"]
    assert "expire_at" in res["data"]
    # storage_path and filename should NOT be in the top level anymore
    assert "file_id" not in res
    assert "filename" not in res
    assert fake_client.bucket_name == "test-bucket"
    assert fake_client.bucket_obj.blobs


def test_resume_upload_success_docx(monkeypatch):
    app = create_app()
    client = TestClient(app)

    fake_client = FakeClient()
    monkeypatch.setattr(resume_service, "_get_gcs_client", lambda: fake_client)
    monkeypatch.setattr(resume_service.settings, "GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(resume_service.settings, "GCP_PROJECT_ID", "test-project")

    files = {"file": ("test.docx", b"fake docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    r = client.post(f"{settings.API_PREFIX}/resumes/", files=files)

    assert r.status_code == 201, r.text
    assert r.json()["data"]["session_id"]


def test_resume_upload_reject_exe(monkeypatch):
    app = create_app()
    client = TestClient(app)

    # Need to mock settings even for failures if validation triggers
    monkeypatch.setattr(resume_service.settings, "GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(resume_service.settings, "GCP_PROJECT_ID", "test-project")

    files = {"file": ("test.exe", b"hello", "application/x-msdownload")}
    r = client.post(f"{settings.API_PREFIX}/resumes/", files=files)

    assert r.status_code == 400, r.text
