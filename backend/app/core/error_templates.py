"""
Error Templates Module

Provides standardized error messages and response formatting for consistent
API error handling across the application.

All error responses follow the format specified in Design Doc 4.2.1:
{
    "code": <HTTP status code>,
    "status": "error",
    "detail": "<Error message>"
}

Usage Example:
    from app.core.error_templates import ErrorTemplate, FILE_TOO_LARGE
    
    # Raise with template
    raise HTTPException(
        status_code=FILE_TOO_LARGE.code,
        detail=FILE_TOO_LARGE.detail
    )
    
    # Or use format_error_detail for dynamic messages
    raise HTTPException(
        status_code=400,
        detail=format_error_detail("Invalid parameter", param="session_id")
    )
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ErrorTemplate:
    """
    Template for standardized error responses.
    
    Attributes:
        code: HTTP status code
        status: Response status (typically "error")
        detail: Human-readable error message
        internal_message: Optional message for logging (not sent to client)
    """
    code: int
    status: str
    detail: str
    internal_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "code": self.code,
            "status": self.status,
            "detail": self.detail
        }


# ============================================================================
# File Upload Errors (400-series)
# ============================================================================

FILE_TOO_LARGE = ErrorTemplate(
    code=400,
    status="error",
    detail="File size exceeds the maximum limit. Please upload a file smaller than the allowed size.",
    internal_message="File size validation failed"
)

INVALID_FILE_TYPE = ErrorTemplate(
    code=400,
    status="error",
    detail="Unsupported file type. Please upload a PDF or DOCX file.",
    internal_message="File extension validation failed"
)

MISSING_FILE = ErrorTemplate(
    code=400,
    status="error",
    detail="No file provided. Please select a file to upload.",
    internal_message="File parameter missing from request"
)

EMPTY_FILE = ErrorTemplate(
    code=400,
    status="error",
    detail="The uploaded file is empty. Please upload a valid resume file.",
    internal_message="File content is empty"
)

SCANNED_PDF_NOT_SUPPORTED = ErrorTemplate(
    code=422,
    status="error",
    detail="Scanned PDFs are not supported. Please upload a text-based PDF.",
    internal_message="PDF has no extractable text"
)

INVALID_PDF_FORMAT = ErrorTemplate(
    code=422,
    status="error",
    detail="Invalid PDF format. The file may be corrupted or not a valid PDF.",
    internal_message="PDF parsing failed"
)

PDF_READ_ERROR = ErrorTemplate(
    code=422,
    status="error",
    detail="Could not read the PDF file. Please ensure it is not corrupted or password-protected.",
    internal_message="PDF file I/O error"
)

RESUME_EMPTY_CONTENT = ErrorTemplate(
    code=400,
    status="error",
    detail="Resume file is empty or could not be read. Please upload a valid resume.",
    internal_message="Resume content extraction returned empty string"
)

# ============================================================================
# Session Errors (400, 404)
# ============================================================================

INVALID_SESSION_ID = ErrorTemplate(
    code=400,
    status="error",
    detail="Invalid session ID format. Session IDs must be valid UUIDs.",
    internal_message="Session ID failed UUID validation"
)

SESSION_NOT_FOUND = ErrorTemplate(
    code=404,
    status="error",
    detail="Session not found. The session may have expired or never existed.",
    internal_message="No blob found for session ID in GCS"
)

SESSION_EXPIRED = ErrorTemplate(
    code=404,
    status="error",
    detail="Session expired. Please upload your resume again.",
    internal_message="Session expiration timestamp passed"
)

# ============================================================================
# LLM Service Errors (500-series)
# ============================================================================

LLM_SERVICE_UNAVAILABLE = ErrorTemplate(
    code=503,
    status="error",
    detail="AI service temporarily unavailable. Please try again later.",
    internal_message="LLM provider returned 503 or connection failed"
)

LLM_RATE_LIMIT = ErrorTemplate(
    code=429,
    status="error",
    detail="Too many requests. Please wait a moment and try again.",
    internal_message="LLM provider rate limit exceeded"
)

LLM_INVALID_RESPONSE = ErrorTemplate(
    code=502,
    status="error",
    detail="AI service returned an invalid response. Please try again.",
    internal_message="Failed to parse LLM response or malformed JSON"
)

LLM_AUTHENTICATION_ERROR = ErrorTemplate(
    code=500,
    status="error",
    detail="AI service authentication failed. Please contact support.",
    internal_message="LLM API key invalid or expired"
)

LLM_TIMEOUT = ErrorTemplate(
    code=504,
    status="error",
    detail="AI service request timed out. Please try again.",
    internal_message="LLM request exceeded timeout threshold"
)

LLM_GENERIC_ERROR = ErrorTemplate(
    code=500,
    status="error",
    detail="An unexpected error occurred with the AI service. Please try again.",
    internal_message="Uncategorized LLM exception"
)

# ============================================================================
# GCS Errors (500-series)
# ============================================================================

GCS_UPLOAD_FAILED = ErrorTemplate(
    code=500,
    status="error",
    detail="Failed to upload file to storage. Please try again.",
    internal_message="GCS blob upload operation failed"
)

GCS_DOWNLOAD_FAILED = ErrorTemplate(
    code=500,
    status="error",
    detail="Failed to retrieve file from storage. Please try again.",
    internal_message="GCS blob download operation failed"
)

GCS_AUTHENTICATION_ERROR = ErrorTemplate(
    code=500,
    status="error",
    detail="Storage authentication failed. Please contact support.",
    internal_message="GCS credentials invalid or missing permissions"
)

GCS_BUCKET_NOT_FOUND = ErrorTemplate(
    code=500,
    status="error",
    detail="Storage configuration error. Please contact support.",
    internal_message="GCS bucket does not exist or is inaccessible"
)

# ============================================================================
# Request Validation Errors (400)
# ============================================================================

MISSING_REQUIRED_FIELD = ErrorTemplate(
    code=400,
    status="error",
    detail="Missing required field in request. Please check your input.",
    internal_message="Required field validation failed"
)

INVALID_REQUEST_FORMAT = ErrorTemplate(
    code=400,
    status="error",
    detail="Invalid request format. Please check the API documentation.",
    internal_message="Request body does not match expected schema"
)

MISSING_JOB_DESCRIPTION = ErrorTemplate(
    code=400,
    status="error",
    detail="Job description is required for this operation.",
    internal_message="job_description field is missing or empty"
)

# ============================================================================
# Content Moderation Errors (400)
# ============================================================================

CONTENT_MODERATION_INPUT_BLOCKED = ErrorTemplate(
    code=400,
    status="error",
    detail="Content moderation failed: your input contains inappropriate material (violence, sexual, hate speech, or prompt injection). Please revise and try again.",
    internal_message="Input content moderation check failed"
)

CONTENT_MODERATION_OUTPUT_BLOCKED = ErrorTemplate(
    code=500,
    status="error",
    detail="Content moderation failed: the AI-generated response did not pass safety checks. Please try again with different input.",
    internal_message="Output content moderation check failed"
)

# ============================================================================
# Generic Errors (500)
# ============================================================================

INTERNAL_SERVER_ERROR = ErrorTemplate(
    code=500,
    status="error",
    detail="An unexpected error occurred. Please try again or contact support.",
    internal_message="Unhandled exception in application"
)


# ============================================================================
# Helper Functions
# ============================================================================

def format_error_detail(base_message: str, **kwargs) -> str:
    """
    Format error detail message with dynamic values.
    
    Args:
        base_message: Base error message template
        **kwargs: Key-value pairs to format into the message
        
    Returns:
        str: Formatted error message
        
    Example:
        >>> format_error_detail("File size {size}MB exceeds limit", size=10)
        "File size 10MB exceeds limit"
    """
    try:
        return base_message.format(**kwargs)
    except KeyError:
        return base_message


def get_error_response_dict(
    template: ErrorTemplate,
    detail_override: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate standardized error response dictionary.
    
    Args:
        template: ErrorTemplate to use
        detail_override: Optional custom detail message (overrides template)
        data: Optional additional data to include in response
        
    Returns:
        Dict containing code, status, detail, and optional data
        
    Example:
        >>> response = get_error_response_dict(
        ...     FILE_TOO_LARGE,
        ...     detail_override="File size 10MB exceeds 5MB limit"
        ... )
        >>> response
        {"code": 400, "status": "error", "detail": "File size 10MB exceeds 5MB limit"}
    """
    response = {
        "code": template.code,
        "status": template.status,
        "detail": detail_override or template.detail
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def create_http_exception_from_template(
    template: ErrorTemplate,
    detail_override: Optional[str] = None
):
    """
    Create FastAPI HTTPException from an ErrorTemplate.
    
    Args:
        template: ErrorTemplate to convert
        detail_override: Optional custom detail message
        
    Returns:
        HTTPException: Ready to raise exception
        
    Example:
        >>> raise create_http_exception_from_template(SESSION_EXPIRED)
    """
    from fastapi import HTTPException
    
    return HTTPException(
        status_code=template.code,
        detail=detail_override or template.detail
    )
