"""
Document Parser Service Module

Handles parsing of various document formats (PDF, DOCX, DOC, TXT) to text/markdown.
"""

from .document_parser import (
    parse_pdf_to_markdown,
    parse_docx_to_markdown,
    parse_doc_to_text,
    parse_txt_to_text,
)

__all__ = [
    "parse_pdf_to_markdown",
    "parse_docx_to_markdown",
    "parse_doc_to_text",
    "parse_txt_to_text",
]
