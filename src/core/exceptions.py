"""Custom exception types for the service."""


class TokenServiceError(Exception):
    """Raised when the token service is unreachable or returns an error."""


class ZohoAPIError(Exception):
    """Raised when the Zoho Desk API returns a non-success response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Zoho API {status_code}: {detail}")
