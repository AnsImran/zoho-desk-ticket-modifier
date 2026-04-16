"""Router for ticket field update operations."""

import logging

from fastapi import APIRouter, HTTPException

from src.core.exceptions import TokenServiceError, ZohoAPIError
from src.core.zoho_client import update_ticket
from src.schemas.tickets import UpdateFieldRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.patch("/{ticket_id}")
def update_ticket_field(ticket_id: str, body: UpdateFieldRequest) -> dict:
    """Update a single field on a Zoho Desk ticket."""
    try:
        return update_ticket(ticket_id, {body.field_name: body.value})
    except TokenServiceError as exc:
        raise HTTPException(status_code=503, detail="Token service unavailable") from exc
    except ZohoAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
