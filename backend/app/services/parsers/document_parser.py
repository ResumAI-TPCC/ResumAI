"""
Document Parser Service

Handles parsing of various document formats to text or markdown.
Supports: PDF, DOCX, DOC, TXT
"""

from __future__ import annotations

import io

import docx
from fastapi import HTTPException, status
from pypdf import PdfReader

from app.core.error_templates import (
    EMPTY_FILE,
    INVALID_PDF_FORMAT,
    PDF_READ_ERROR,
    SCANNED_PDF_NOT_SUPPORTED,
)


def parse_pdf_to_markdown(content: bytes) -> str:
    """
    Parse text-based PDF to plain text.
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        str: Extracted text from PDF
        
    Raises:
        HTTPException: If PDF is scanned, unreadable, or contains no text
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        full_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            full_text.append(text)
        
        result = "\n".join(full_text).strip()
        if not result:
            raise HTTPException(
                status_code=SCANNED_PDF_NOT_SUPPORTED.code,
                detail=SCANNED_PDF_NOT_SUPPORTED.detail,
            )
        return result
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
        # PDF parsing/format errors
        raise HTTPException(
            status_code=INVALID_PDF_FORMAT.code,
            detail=INVALID_PDF_FORMAT.detail,
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF parsing error: {str(exc)}",
        ) from exc


def parse_docx_to_markdown(content: bytes) -> str:
    """
    Parse DOCX to simple Markdown format.
    
    Converts Word document styles to Markdown:
    - Heading 1/2/3 → #, ##, ###
    - List items → *
    - Bold text → **bold**
    
    Args:
        content: DOCX file content as bytes
        
    Returns:
        str: Markdown-formatted text
        
    Raises:
        HTTPException: If DOCX is invalid, empty, or unreadable
    """
    try:
        doc = docx.Document(io.BytesIO(content))
        md_lines = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Simple style to markdown mapping
            style_name = para.style.name.lower()
            if style_name.startswith('heading 1'):
                md_lines.append(f"# {text}")
            elif style_name.startswith('heading 2'):
                md_lines.append(f"## {text}")
            elif style_name.startswith('heading 3'):
                md_lines.append(f"### {text}")
            elif para.style.name.startswith('List'):
                md_lines.append(f"* {text}")
            else:
                # Process inline formatting like bold
                processed_text = ""
                for run in para.runs:
                    run_text = run.text
                    if run.bold:
                        processed_text += f"**{run_text}**"
                    else:
                        processed_text += run_text
                md_lines.append(processed_text)
        
        result = "\n\n".join(md_lines).strip()
        if not result:
            raise HTTPException(
                status_code=EMPTY_FILE.code,
                detail=EMPTY_FILE.detail,
            )
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (IOError, OSError) as exc:
        # File I/O errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read DOCX file: {str(exc)}",
        ) from exc
    except (AttributeError, KeyError) as exc:
        # DOCX structure/format errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid DOCX format: {str(exc)}",
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DOCX parsing error: {str(exc)}",
        ) from exc


def parse_doc_to_text(content: bytes) -> str:
    """
    Parse legacy .doc file to plain text.
    
    Attempts to extract text from binary .doc format using olefile library.
    Falls back to brute-force text extraction if olefile not available.
    
    Args:
        content: DOC file content as bytes
        
    Returns:
        str: Extracted text
        
    Raises:
        HTTPException: If file cannot be parsed or contains no text
        
    Note:
        Recommend users convert .doc to .docx for better results.
    """
    try:
        import olefile
        ole = olefile.OleFileIO(io.BytesIO(content))
        # WordDocument stream contains the raw text in .doc files
        if ole.exists("WordDocument"):
            stream = ole.openstream("WordDocument")
            raw = stream.read()
            text = raw.decode("utf-8", errors="ignore")
            result = "".join(
                c if c.isprintable() or c in "\n\r\t" else " " for c in text
            ).strip()
            if result:
                return result
        # Fallback: try to read any text from all streams
        text = content.decode("utf-8", errors="ignore")
        result = "".join(
            c if c.isprintable() or c in "\n\r\t" else " " for c in text
        ).strip()
        if result:
            return result
        raise ValueError("No text extracted")
    except ImportError:
        # olefile not installed: brute-force text extraction
        text = content.decode("utf-8", errors="ignore")
        result = "".join(
            c if c.isprintable() or c in "\n\r\t" else " " for c in text
        ).strip()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to parse .doc file. Please convert to .docx format.",
            )
        return result
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse .doc file: {exc}. Please convert to .docx format.",
        ) from exc


def parse_txt_to_text(content: bytes) -> str:
    """
    Parse plain text file.
    
    Args:
        content: Text file content as bytes
        
    Returns:
        str: Decoded text content
        
    Note:
        Uses UTF-8 decoding with error replacement for invalid characters.
    """
    return content.decode("utf-8", errors="replace")
