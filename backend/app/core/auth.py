"""
Firebase authentication dependencies.
"""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from typing import Any, Dict, Optional

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials as firebase_credentials

from app.core.config import settings
from app.schemas.auth_schema import CurrentUserClaims

bearer_scheme = HTTPBearer(auto_error=False)


class FirebaseAuthConfigurationError(RuntimeError):
    """Raised when Firebase Admin cannot be initialized."""


def _decode_service_account_key(raw_key: str) -> Dict[str, Any]:
    payload = raw_key.strip()
    if not payload:
        raise ValueError("Empty Firebase service account key")

    if not payload.startswith("{"):
        payload = base64.b64decode(payload).decode("utf-8")

    info = json.loads(payload)
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    return info


def _build_firebase_credential() -> firebase_credentials.Base:
    if settings.FIREBASE_SERVICE_ACCOUNT_KEY.strip():
        info = _decode_service_account_key(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
        return firebase_credentials.Certificate(info)

    if settings.FIREBASE_CREDENTIALS_PATH.strip():
        return firebase_credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    return firebase_credentials.ApplicationDefault()


def _firebase_options() -> Optional[Dict[str, str]]:
    project_id = settings.FIREBASE_PROJECT_ID or settings.GCP_PROJECT_ID
    if not project_id:
        return None

    return {"projectId": project_id}


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    """Return the default Firebase app, initializing it on first use."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    try:
        return firebase_admin.initialize_app(
            credential=_build_firebase_credential(),
            options=_firebase_options(),
        )
    except Exception as exc:  # pragma: no cover - exact SDK errors vary by env
        raise FirebaseAuthConfigurationError(
            "Firebase Admin is not configured correctly."
        ) from exc


def normalize_firebase_claims(decoded_token: Dict[str, Any]) -> CurrentUserClaims:
    """Convert Firebase decoded token payload into the API's user shape."""
    uid = decoded_token.get("uid") or decoded_token.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing a user id.",
        )

    return CurrentUserClaims(
        firebase_uid=str(uid),
        email=decoded_token.get("email"),
        display_name=decoded_token.get("name"),
        email_verified=bool(decoded_token.get("email_verified", False)),
        claims=decoded_token,
    )


def verify_firebase_id_token(token: str) -> CurrentUserClaims:
    """Verify a Firebase ID token and return normalized user claims."""
    if is_valid_dev_auth_token(token):
        return build_dev_user_claims()

    try:
        decoded_token = firebase_auth.verify_id_token(
            token,
            app=get_firebase_app(),
            check_revoked=True,
        )
    except FirebaseAuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        ) from exc
    except (
        firebase_auth.ExpiredIdTokenError,
        firebase_auth.InvalidIdTokenError,
        firebase_auth.RevokedIdTokenError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc

    return normalize_firebase_claims(decoded_token)


def is_valid_dev_auth_token(token: str) -> bool:
    """Return true when a configured local-only dev auth token was provided."""
    return bool(settings.DEBUG and settings.DEV_AUTH_TOKEN and token == settings.DEV_AUTH_TOKEN)


def build_dev_user_claims() -> CurrentUserClaims:
    """Build a local development user without calling Firebase Admin."""
    return CurrentUserClaims(
        firebase_uid=settings.DEV_AUTH_UID,
        email=settings.DEV_AUTH_EMAIL or "test@resumai.local",
        display_name=settings.DEV_AUTH_DISPLAY_NAME,
        email_verified=True,
        claims={
            "uid": settings.DEV_AUTH_UID,
            "email": settings.DEV_AUTH_EMAIL or "test@resumai.local",
            "name": settings.DEV_AUTH_DISPLAY_NAME,
            "email_verified": True,
            "auth_provider": "local-dev-whitelist",
        },
    )


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUserClaims:
    """FastAPI dependency requiring a valid Firebase bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer authentication token.",
        )

    return verify_firebase_id_token(credentials.credentials)
