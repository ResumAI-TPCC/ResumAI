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
    """Custom PDF class with resume styling"""
    
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
    
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def _preprocess_content(content: str) -> str:
    """Remove LLM intro text, markdown markers, and page markers from content"""
    lines = content.split('\n')
    result = []
    started = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip markdown code block markers and variations
        if stripped.startswith('```') or stripped.endswith('```'):
            continue
        if '`markdown' in stripped.lower() or stripped.lower() == 'markdown':
            continue
        if stripped.startswith('`') and len(stripped) < 15:
            continue
            
        # Skip LLM intro lines
        if not started:
            if stripped.startswith('---') or stripped.startswith('#') or stripped.startswith('**'):
                started = True
            elif any(kw in stripped.lower() for kw in ['here\'s', 'here is', 'rewritten', 'optimized version']):
                continue
            else:
                started = True
        
        if not started:
            continue
            
        # Skip page markers
        if re.match(r'^Page \d+$', stripped):
            continue
        if re.match(r'^--\s*\d+\s*of\s*\d+\s*--$', stripped):
            continue
            
        result.append(line)
    
    return '\n'.join(result)


def markdown_to_pdf(markdown_content: str) -> bytes:
    """
    Convert Markdown text to a PDF byte stream.

    Args:
        markdown_content: The optimized resume in Markdown format.

    Returns:
        PDF content as bytes.
    """
    # Preprocess to remove LLM intro and page markers
    markdown_content = _preprocess_content(markdown_content)
    
    pdf = ResumePDF()
    
    lines = markdown_content.split('\n')
    is_first_name = True
    
    for line in lines:
        line = line.strip()
        
        if not line:
            pdf.ln(1)
            continue
        
        # Skip horizontal rules (---)
        if re.match(r'^-{3,}$', line):
            continue
        
        # H1 - Name/Title (centered, no underline)
        if line.startswith('# '):
            text = line[2:].strip()
            text = _clean_markdown(text)
            pdf.set_font('Helvetica', 'B', 18)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(0, 10, text, align='C', new_x='LMARGIN', new_y='NEXT')
            pdf.ln(2)
            
        # H2 - Section headers (with underline)
        elif line.startswith('## '):
            text = line[3:].strip()
            text = _clean_markdown(text)
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(0, 7, text.upper(), new_x='LMARGIN', new_y='NEXT')
            pdf.set_draw_color(160, 160, 160)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(2)
            
        # H3 - Sub-sections (with underline)
        elif line.startswith('### '):
            text = line[4:].strip()
            text = _clean_markdown(text)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(51, 51, 51)
            try:
                pdf.cell(0, 6, text, new_x='LMARGIN', new_y='NEXT')
                pdf.set_draw_color(200, 200, 200)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(1)
            except Exception:
                pass
        
        # Bold section headers like **Professional Summary** or **Name**
        elif line.startswith('**') and line.endswith('**') and len(line) < 50:
            text = line[2:-2].strip()
            text = _clean_markdown(text)
            
            # First bold line is likely the name - no underline, centered
            if is_first_name:
                pdf.set_font('Helvetica', 'B', 18)
                pdf.set_text_color(26, 26, 46)
                try:
                    pdf.cell(0, 10, text, align='C', new_x='LMARGIN', new_y='NEXT')
                except Exception:
                    pass
                pdf.ln(2)
                is_first_name = False
            else:
                # Section header with underline
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(26, 26, 46)
                try:
                    pdf.cell(0, 7, text.upper(), new_x='LMARGIN', new_y='NEXT')
                except Exception:
                    pass
                pdf.set_draw_color(160, 160, 160)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(2)
            
        # Bullet points
        elif line.startswith('* ') or line.startswith('- '):
            text = line[2:].strip()
            text = _clean_markdown(text)
            if text:
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(34, 34, 34)
                pdf.set_x(24)
                try:
                    pdf.multi_cell(0, 4, f"* {text}")
                except Exception:
                    pass
        
        # Name line (first non-empty, non-header line after ---)
        elif is_first_name and not line.startswith('#') and not line.startswith('*'):
            text = _clean_markdown(line)
            if text and len(text) < 50:
                pdf.set_font('Helvetica', 'B', 18)
                pdf.set_text_color(26, 26, 46)
                try:
                    pdf.cell(0, 10, text, align='C', new_x='LMARGIN', new_y='NEXT')
                except Exception:
                    pass
                pdf.ln(2)
                is_first_name = False
            else:
                is_first_name = False
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(34, 34, 34)
                try:
                    pdf.multi_cell(0, 4, text)
                except Exception:
                    pass
            
        # Regular text
        else:
            text = _clean_markdown(line)
            if text:
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(34, 34, 34)
                try:
                    pdf.multi_cell(0, 4, text)
                except Exception:
                    pass
    
    pdf_bytes = pdf.output()
    logger.info("PDF generated successfully (%d bytes)", len(pdf_bytes))
    return bytes(pdf_bytes)


def _clean_markdown(text: str) -> str:
    """Remove markdown formatting and special characters from text"""
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Links [text](url)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Inline code `text`
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Filter special characters that Helvetica cannot render
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


def markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown text to an HTML string for preview.
    Simple implementation without external dependencies.
    """
    html = markdown_content
    # Basic conversions
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'^[\*\-] (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = html.replace('\n', '<br>')
    return html
