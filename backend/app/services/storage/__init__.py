"""
Storage Service Module

Handles Google Cloud Storage operations for resume file management.
"""

from .gcs_service import (
    get_gcs_client,
    upload_file_to_gcs,
    download_file_from_gcs,
    build_service_account_credentials,
)

__all__ = [
    "get_gcs_client",
    "upload_file_to_gcs",
    "download_file_from_gcs",
    "build_service_account_credentials",
]
