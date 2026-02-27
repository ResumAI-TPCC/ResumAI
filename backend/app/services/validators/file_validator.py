"""
File Validator Service

Validates file names, extensions, and content for security and format compliance.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from fastapi import HTTPException, status
from pypdf import PdfReader

from app.core.error_templates import (
    EMPTY_FILE,
    INVALID_FILE_TYPE,
    INVALID_PDF_FORMAT,
    MISSING_FILE,
    PDF_READ_ERROR,
    SCANNED_PDF_NOT_SUPPORTED,
)

# Allowed file extensions per design doc
ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt"}


def validate_filename(filename: str) -> None:
    """
    Validate file extension and name.
    
    Args:
        filename: Name of the file to validate
        
    Raises:
        HTTPException(400): If filename is missing or has invalid extension
        
    Example:
        >>> validate_filename("resume.pdf")  # OK
        >>> validate_filename("resume.exe")  # Raises HTTPException
    """
    if not filename:
        raise HTTPException(
            status_code=MISSING_FILE.code,
            detail=MISSING_FILE.detail,
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=INVALID_FILE_TYPE.code,
            detail=INVALID_FILE_TYPE.detail,
        )


def clean_filename(filename: str) -> str:
    """
    Basic filename cleaning to remove unsafe characters.
    
    Replaces spaces and non-alphanumeric characters (except . - _) with underscores.
    Preserves file extension.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Cleaned filename safe for storage
        
    Example:
        >>> clean_filename("My Resume (2024).pdf")
        'My_Resume_2024.pdf'
        >>> clean_filename("résumé.docx")
        'rsum.docx'
    """
    path = Path(filename)
    stem = path.stem
    ext = path.suffix

    # Replace non-alphanumeric/space/dash with nothing, then spaces/dashes with underscore
    clean_stem = re.sub(r"[^\w\s-]", "", stem).strip()
    clean_stem = re.sub(r"[-\s]+", "_", clean_stem)

    # Fallback if stem becomes empty
    if not clean_stem:
        clean_stem = "resume"

    return f"{clean_stem}{ext}"


def validate_pdf_content(content: bytes) -> None:
    """
    Check if PDF is text-based and contains extractable text.
    
    Rejects scanned PDFs (images) that have no extractable text.
    Used during upload validation to ensure PDF can be processed.
    
    Args:
        content: PDF file content as bytes
        
    Raises:
        HTTPException(422): If PDF is scanned, empty, or unreadable
        
    Note:
        This is a quick validation check. For full text extraction,
        use parse_pdf_to_markdown from parsers service.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        
        if len(reader.pages) == 0:
            raise HTTPException(
                status_code=EMPTY_FILE.code,
                detail=EMPTY_FILE.detail,
            )
        
        # Check first page for extractable text
        first_page_text = reader.pages[0].extract_text() or ""
        if not first_page_text.strip():
            raise HTTPException(
                status_code=SCANNED_PDF_NOT_SUPPORTED.code,
                detail=SCANNED_PDF_NOT_SUPPORTED.detail,
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (IOError, OSError) as exc:
        # File I/O errors
        raise HTTPException(
            status_code=PDF_READ_ERROR.code,
            detail=PDF_READ_ERROR.detail,
        ) from exc
    except ValueError as exc:
        # PDF parsing errors
        raise HTTPException(
            status_code=INVALID_PDF_FORMAT.code,
            detail=INVALID_PDF_FORMAT.detail,
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF validation failed: {str(exc)}",
        ) from exc
