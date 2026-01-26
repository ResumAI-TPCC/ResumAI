"""
Custom exceptions for LLM Service
"""


class LLMException(Exception):
    """Base exception for LLM service"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LLMAuthenticationError(LLMException):
    """Raised when API key authentication fails"""

    def __init__(self, message: str = "LLM API authentication failed"):
        super().__init__(message, status_code=401)


class LLMRateLimitError(LLMException):
    """Raised when API rate limit is exceeded"""

    def __init__(self, message: str = "LLM API rate limit exceeded"):
        super().__init__(message, status_code=429)


class LLMTimeoutError(LLMException):
    """Raised when API request times out"""

    def __init__(self, message: str = "LLM API request timeout"):
        super().__init__(message, status_code=504)


class LLMResponseError(LLMException):
    """Raised when response parsing fails"""

    def __init__(self, message: str = "Failed to parse LLM response"):
        super().__init__(message, status_code=502)


class LLMServiceUnavailableError(LLMException):
    """Raised when LLM service is unavailable"""

    def __init__(self, message: str = "LLM service is unavailable"):
        super().__init__(message, status_code=503)
