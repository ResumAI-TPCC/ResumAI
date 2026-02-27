"""
File Service - Generate and encode resume files
"""

import base64


def generate_markdown_file(content: str) -> bytes:
    """Generate Markdown file from content"""
    return content.encode("utf-8")


def encode_to_base64(file_bytes: bytes) -> str:
    """Encode file bytes to base64 string"""
    return base64.b64encode(file_bytes).decode("utf-8")


def generate_and_encode_resume(content: str) -> str:
    """Generate markdown file and return base64 encoded string"""
    file_bytes = generate_markdown_file(content)
    return encode_to_base64(file_bytes)
