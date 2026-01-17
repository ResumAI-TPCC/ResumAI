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
    monkeypatch.setattr(resume_service.settings, "gcs_bucket_name", "test-bucket")
    monkeypatch.setattr(resume_service.settings, "gcs_object_prefix", "resumes")

    files = {"file": ("test.pdf", b"%PDF-1.4\nfake\n", "application/pdf")}
    r = client.post(f"{settings.api_prefix}/resume/", files=files)

    assert r.status_code == 200, r.text
    data = r.json()
    assert "file_id" in data
    assert data["filename"] == "test.pdf"
    assert "storage_path" in data
    assert data["storage_path"].startswith("gs://test-bucket/resumes/")
    assert fake_client.bucket_name == "test-bucket"
    assert fake_client.bucket_obj.blobs


def test_resume_upload_success_txt(monkeypatch):
    app = create_app()
    client = TestClient(app)

    fake_client = FakeClient()
    monkeypatch.setattr(resume_service, "_get_gcs_client", lambda: fake_client)
    monkeypatch.setattr(resume_service.settings, "gcs_bucket_name", "test-bucket")

    files = {"file": ("test.txt", b"hello world", "text/plain")}
    r = client.post(f"{settings.api_prefix}/resume/", files=files)

    assert r.status_code == 200, r.text
    assert r.json()["filename"] == "test.txt"


def test_resume_upload_reject_exe():
    app = create_app()
    client = TestClient(app)

    files = {"file": ("test.exe", b"hello", "application/x-msdownload")}
    r = client.post(f"{settings.api_prefix}/resume/", files=files)

    assert r.status_code == 400, r.text
