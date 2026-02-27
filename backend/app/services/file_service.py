"""
File Service - Generate and encode resume files

This module handles file generation and encoding for resume downloads.
Optimized resume content from the LLM is converted to downloadable file formats.

Usage Example:
    from app.services.file_service import generate_and_encode_resume
    
    # Generate and encode resume for download
    optimized_content = "# John Doe\n\nSoftware Engineer..."
    encoded_file = generate_and_encode_resume(optimized_content)
    
    # Return to frontend for download
    return {"encoded_file": encoded_file}
"""

import base64


def generate_markdown_file(content: str) -> bytes:
    """
    Convert resume content string to UTF-8 encoded bytes.
    
    This is a simple text-to-bytes conversion that prepares markdown
    content for file download or further processing.
    
    Args:
        content: Resume content as a string (typically Markdown format)
        
    Returns:
        bytes: UTF-8 encoded content
        
    Example:
        >>> content = "# John Doe\n\nSoftware Engineer"
        >>> file_bytes = generate_markdown_file(content)
        >>> isinstance(file_bytes, bytes)
        True
    """
    return content.encode("utf-8")


def encode_to_base64(file_bytes: bytes) -> str:
    """
    Encode file bytes to base64 string for transport.
    
    Base64 encoding allows binary data to be safely transmitted
    as text in JSON responses. The frontend can decode this back
    to bytes for file download.
    
    Args:
        file_bytes: File content as bytes
        
    Returns:
        str: Base64 encoded string
        
    Example:
        >>> file_bytes = b"Hello World"
        >>> encoded = encode_to_base64(file_bytes)
        >>> encoded
        'SGVsbG8gV29ybGQ='
    """
    return base64.b64encode(file_bytes).decode("utf-8")


def generate_and_encode_resume(content: str) -> str:
    """
    Generate markdown file and return base64 encoded string.
    
    This is a convenience function that combines markdown generation
    and base64 encoding in one step. Use this for the optimize endpoint
    to prepare resume content for download.
    
    Args:
        content: Resume content as string (Markdown format)
        
    Returns:
        str: Base64 encoded file content ready for JSON response
        
    Raises:
        UnicodeEncodeError: If content contains invalid UTF-8 characters
        
    Example:
        >>> content = "# Jane Smith\n\n## Experience\n- Software Engineer at TechCorp"
        >>> encoded = generate_and_encode_resume(content)
        >>> # Frontend can decode and trigger download
    """
    file_bytes = generate_markdown_file(content)
    return encode_to_base64(file_bytes)
