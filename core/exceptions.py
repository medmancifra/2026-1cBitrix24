"""
Custom exceptions for the Bitrix24 core module.
"""


class Bitrix24Error(Exception):
    """Base exception for all Bitrix24 errors."""
    pass


class AuthError(Bitrix24Error):
    """Raised when authentication fails."""
    pass


class APIError(Bitrix24Error):
    """Raised when the Bitrix24 API returns an error response."""

    def __init__(self, error_code: str, error_description: str, response: dict = None):
        self.error_code = error_code
        self.error_description = error_description
        self.response = response or {}
        super().__init__(f"[{error_code}] {error_description}")


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""
    pass


class NotFoundError(APIError):
    """Raised when a requested resource is not found."""
    pass
