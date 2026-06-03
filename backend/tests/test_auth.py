"""
Tests for Firebase Auth API wiring.
"""

from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import get_current_user_claims
from app.core.config import settings
from app.main import create_app
from app.schemas.auth_schema import CurrentUserClaims


def _user() -> CurrentUserClaims:
    return CurrentUserClaims(
        firebase_uid="firebase-user-123",
        email="user@example.com",
        display_name="User Example",
        email_verified=True,
        claims={"uid": "firebase-user-123"},
    )


def test_me_returns_current_user():
    app = create_app()
    app.dependency_overrides[get_current_user_claims] = _user
    client = TestClient(app)

    response = client.get(f"{settings.API_PREFIX}/me")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["firebase_uid"] == "firebase-user-123"
    assert data["email"] == "user@example.com"
    assert data["email_verified"] is True


def test_me_requires_bearer_token_without_override():
    client = TestClient(create_app())

    response = client.get(f"{settings.API_PREFIX}/me")

    assert response.status_code == 401
    assert "bearer" in response.json()["detail"].lower()


def test_me_rejects_invalid_token():
    client = TestClient(create_app())

    with patch(
        "app.core.auth.verify_firebase_id_token",
        side_effect=HTTPException(status_code=401, detail="Invalid token"),
    ):
        response = client.get(
            f"{settings.API_PREFIX}/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_resume_routes_require_auth_without_override():
    client = TestClient(create_app())

    response = client.post(f"{settings.API_PREFIX}/resumes/analyze", json={})

    assert response.status_code == 401
