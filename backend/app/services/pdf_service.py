"""
PDF Service - Convert Markdown content to PDF

Converts LLM-generated optimized resume (Markdown) into a downloadable PDF file.
Uses fpdf2 for PDF generation with professional resume styling.
"""

from __future__ import annotations

import logging
import re

from fpdf import FPDF

logger = logging.getLogger(__name__)


class ResumePDF(FPDF):
    """Custom PDF class with resume styling."""

    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _preprocess_content(content: str) -> str:
    """Remove LLM intro text, markdown code-block markers, and page markers."""
    lines = content.split("\n")
    result = []
    started = False

    for line in lines:
        stripped = line.strip()

        # Skip markdown code block markers
        if stripped.startswith("```") or stripped.endswith("```"):
            continue
        if "markdown" in stripped.lower() and len(stripped) < 15:
            continue
        if stripped.startswith("`") and len(stripped) < 15:
            continue

        # Skip LLM intro lines before the real resume content starts
        if not started:
            if stripped.startswith("---") or stripped.startswith("#") or stripped.startswith("**"):
                started = True
            elif any(kw in stripped.lower() for kw in ["here's", "here is", "rewritten", "optimized version"]):
                continue
            else:
                started = True

        if not started:
            continue

        # Skip page markers
        if re.match(r"^Page \d+$", stripped):
            continue
        if re.match(r"^--\s*\d+\s*of\s*\d+\s*--$", stripped):
            continue

        result.append(line)

    return "\n".join(result)


def _clean_markdown(text: str) -> str:
    """Remove markdown formatting and replace non-latin-1 characters."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Helvetica only supports latin-1; replace unsupported chars
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def markdown_to_pdf(markdown_content: str) -> bytes:
    """
    Convert Markdown text to a professionally styled PDF byte stream.

    Uses fpdf2 to parse Markdown headings, bullet points, and body text
    into an A4 PDF with professional resume typography.

    Args:
        markdown_content: The optimized resume in Markdown format.

    Returns:
        PDF content as bytes.
    """
    markdown_content = _preprocess_content(markdown_content)

    pdf = ResumePDF()

    lines = markdown_content.split("\n")
    is_first_name = True

    for line in lines:
        line = line.strip()

        if not line:
            pdf.ln(1)
            continue

        # Skip horizontal rules
        if re.match(r"^-{3,}$", line):
            continue

        # H1 - Name/Title
        if line.startswith("# "):
            text = _clean_markdown(line[2:].strip())
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(0, 10, text, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # H2 - Section headers
        elif line.startswith("## "):
            text = _clean_markdown(line[3:].strip())
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(0, 7, text.upper(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(160, 160, 160)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)

        # H3 - Sub-sections
        elif line.startswith("### "):
            text = _clean_markdown(line[4:].strip())
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(51, 51, 51)
            pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(1)

        # Standalone bold header like **Professional Summary**
        elif line.startswith("**") and line.endswith("**") and len(line) < 50:
            text = _clean_markdown(line[2:-2].strip())
            if is_first_name:
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(26, 26, 46)
                pdf.cell(0, 10, text, align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                is_first_name = False
            else:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(26, 26, 46)
                pdf.cell(0, 7, text.upper(), new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(160, 160, 160)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(2)

        # Bullet points
        elif line.startswith("* ") or line.startswith("- "):
            text = _clean_markdown(line[2:].strip())
            if text:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(34, 34, 34)
                bullet_indent = pdf.l_margin + 5
                pdf.set_x(bullet_indent)
                pdf.multi_cell(pdf.w - bullet_indent - pdf.r_margin, 4, f"\x95 {text}")

        # First non-header line may be a name
        elif is_first_name and not line.startswith("#") and not line.startswith("*"):
            text = _clean_markdown(line)
            if text and len(text) < 50:
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(26, 26, 46)
                pdf.cell(0, 10, text, align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                is_first_name = False
            else:
                is_first_name = False
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(34, 34, 34)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 4, text)

        # Regular text
        else:
            text = _clean_markdown(line)
            if text:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(34, 34, 34)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 4, text)

    pdf_bytes = pdf.output()
    logger.info("PDF generated successfully (%d bytes)", len(pdf_bytes))
    return bytes(pdf_bytes)


def markdown_to_html(markdown_content: str) -> str:
    """Convert Markdown text to an HTML string for preview."""
    html = markdown_content
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^[\*\-] (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = html.replace("\n", "<br>")
    return html
