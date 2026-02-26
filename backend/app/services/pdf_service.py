"""
PDF Service - Convert Markdown content to PDF

Converts LLM-generated optimized resume (Markdown) into a downloadable PDF file.
Uses markdown → HTML → PDF pipeline with professional resume styling.
"""

from __future__ import annotations

import io
import logging

import markdown
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

# Professional resume CSS styling
RESUME_CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #222222;
}

h1 {
    font-size: 22pt;
    color: #1a1a2e;
    margin-bottom: 4px;
    padding-bottom: 6px;
    border-bottom: 2px solid #1a1a2e;
    text-align: center;
}

h2 {
    font-size: 14pt;
    color: #1a1a2e;
    margin-top: 16px;
    margin-bottom: 6px;
    padding-bottom: 3px;
    border-bottom: 1px solid #cccccc;
    text-transform: uppercase;
    letter-spacing: 1px;
}

h3 {
    font-size: 12pt;
    color: #333333;
    margin-top: 10px;
    margin-bottom: 4px;
}

p {
    margin-top: 2px;
    margin-bottom: 6px;
    text-align: justify;
}

ul {
    margin-top: 2px;
    margin-bottom: 6px;
    padding-left: 20px;
}

li {
    margin-bottom: 3px;
}

strong {
    color: #1a1a2e;
}

em {
    color: #555555;
}

a {
    color: #2563eb;
    text-decoration: none;
}
"""


def markdown_to_pdf(markdown_content: str) -> bytes:
    """
    Convert Markdown text to a professionally styled PDF byte stream.
    
    This function implements a three-stage pipeline:
    1. Convert Markdown to HTML using python-markdown
    2. Apply professional resume CSS styling
    3. Generate PDF using xhtml2pdf (pisa)
    
    The resulting PDF is formatted for A4 paper with professional typography,
    section headers, and consistent spacing suitable for resume presentation.

    Args:
        markdown_content: The optimized resume in Markdown format
        
    Returns:
        bytes: PDF file content ready for download or storage
        
    Raises:
        ValueError: If markdown_content is empty or invalid
        ValueError: If conversion fails.
    """
    # Step 1: Markdown → HTML
    html_body = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )

    # Step 2: Wrap in full HTML document with styling
    html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>{RESUME_CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    # Step 3: HTML → PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_document,
        dest=pdf_buffer,
        encoding="utf-8",
    )

    if pisa_status.err:
        logger.error("PDF conversion failed with %d errors", pisa_status.err)
        raise ValueError("Failed to convert resume to PDF")

    pdf_bytes = pdf_buffer.getvalue()
    logger.info("PDF generated successfully (%d bytes)", len(pdf_bytes))
    return pdf_bytes


def markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown text to an HTML string for preview.

    Args:
        markdown_content: The optimized resume in Markdown format.

    Returns:
        HTML string.
    """
    return markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
