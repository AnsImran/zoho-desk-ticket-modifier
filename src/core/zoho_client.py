"""HTTP client for Zoho Desk API and the internal token service."""

import logging

import httpx

from src.core.config import settings
from src.core.exceptions import TokenServiceError, ZohoAPIError

logger = logging.getLogger(__name__)


def get_access_token() -> str:
    """Fetch a valid access token from the token service."""
    url = settings.token_service_url
    try:
        resp = httpx.get(url, timeout=settings.token_request_timeout)
        resp.raise_for_status()
    except httpx.ConnectError:
        logger.error("Token service unreachable at %s", url)
        raise TokenServiceError(f"Cannot connect to token service at {url}")
    except httpx.TimeoutException:
        logger.error("Token service timed out at %s", url)
        raise TokenServiceError(f"Token service timed out at {url}")
    except httpx.HTTPStatusError as exc:
        logger.error("Token service returned %d: %s", exc.response.status_code, exc.response.text)
        raise TokenServiceError(f"Token service returned {exc.response.status_code}")

    data = resp.json()
    if data.get("is_stale"):
        logger.warning("Token is stale, proceeding anyway")
    return data["access_token"]


def _headers() -> dict[str, str]:
    token = get_access_token()
    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "orgId": settings.zoho_org_id,
        "Content-Type": "application/json",
    }


def update_ticket(ticket_id: str, fields: dict) -> dict:
    """PATCH a Zoho Desk ticket with the given field values."""
    url = f"{settings.zoho_desk_base_url}/tickets/{ticket_id}"
    logger.info("PATCH %s with fields %s", url, list(fields.keys()))

    try:
        resp = httpx.patch(url, headers=_headers(), json=fields, timeout=settings.zoho_request_timeout)
        resp.raise_for_status()
    except httpx.ConnectError:
        logger.error("Cannot reach Zoho Desk API at %s", url)
        raise ZohoAPIError(502, "Cannot reach Zoho Desk API")
    except httpx.TimeoutException:
        logger.error("Zoho Desk API timed out for PATCH %s", url)
        raise ZohoAPIError(504, "Zoho Desk API timed out")
    except httpx.HTTPStatusError as exc:
        logger.error("Zoho API error %d for PATCH %s: %s", exc.response.status_code, url, exc.response.text)
        raise ZohoAPIError(exc.response.status_code, exc.response.text)

    logger.info("Ticket %s updated successfully", ticket_id)
    return resp.json()


def add_private_comment(ticket_id: str, content: str) -> dict:
    """POST a private comment to a Zoho Desk ticket."""
    url = f"{settings.zoho_desk_base_url}/tickets/{ticket_id}/comments"
    logger.info("POST comment on ticket %s", ticket_id)

    try:
        resp = httpx.post(
            url,
            headers=_headers(),
            json={"content": content, "isPublic": False, "contentType": "plainText"},
            timeout=settings.zoho_request_timeout,
        )
        resp.raise_for_status()
    except httpx.ConnectError:
        logger.error("Cannot reach Zoho Desk API at %s", url)
        raise ZohoAPIError(502, "Cannot reach Zoho Desk API")
    except httpx.TimeoutException:
        logger.error("Zoho Desk API timed out for POST %s", url)
        raise ZohoAPIError(504, "Zoho Desk API timed out")
    except httpx.HTTPStatusError as exc:
        logger.error("Zoho API error %d for POST %s: %s", exc.response.status_code, url, exc.response.text)
        raise ZohoAPIError(exc.response.status_code, exc.response.text)

    logger.info("Comment added to ticket %s", ticket_id)
    return resp.json()


def check_token_service() -> bool:
    """Check if the token service is reachable. Used by readiness probe."""
    try:
        resp = httpx.get(settings.token_service_url, timeout=5)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
