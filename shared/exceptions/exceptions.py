"""
shared/exceptions/exceptions.py

Domain-level custom exceptions. Free of any Django/ORM dependency.
These map 1:1 to HTTP status codes in the exception handler.
"""


class AppBaseException(Exception):
    """Base class for all application exceptions."""
    message: str = "An unexpected error occurred."
    status_code: int = 500

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ─────────────────────────────────────────────────
# URL domain exceptions
# ─────────────────────────────────────────────────

class UrlNotFoundError(AppBaseException):
    """Raised when the short code does not exist in the data store."""
    message = "Short URL not found."
    status_code = 404


class UrlExpiredError(AppBaseException):
    """Raised when the short URL exists but has passed its expiry time."""
    message = "This short URL has expired."
    status_code = 410


class UrlInactiveError(AppBaseException):
    """Raised when the short URL has been deactivated."""
    message = "This short URL is no longer active."
    status_code = 410


class ShortCodeCollisionError(AppBaseException):
    """Raised when all collision retry attempts are exhausted."""
    message = "Unable to generate a unique short code. Please try again."
    status_code = 500


class InvalidUrlError(AppBaseException):
    """Raised when the provided URL fails validation (e.g. SSRF block)."""
    message = "The provided URL is invalid or not allowed."
    status_code = 400


class CustomAliasConflictError(AppBaseException):
    """Raised when the requested custom alias is already taken."""
    message = "This custom alias is already in use."
    status_code = 409
