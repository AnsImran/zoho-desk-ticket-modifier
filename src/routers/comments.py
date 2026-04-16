"""Router for private comment operations."""

import logging

from fastapi import APIRouter, HTTPException

from src.core import template_engine
from src.core.exceptions import TokenServiceError, ZohoAPIError
from src.core.zoho_client import add_private_comment
from src.schemas.tickets import CommentTypeInfo, PrivateCommentRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["comments"])


@router.get("/comment-types", response_model=dict[str, CommentTypeInfo])
def list_comment_types() -> dict:
    """List all available private comment template types and their required fields."""
    return template_engine.get_available_types()


@router.post("/comment-types/reload")
def reload_comment_types() -> dict:
    """Hot-reload comment templates from the YAML file on disk."""
    try:
        reloaded = template_engine.reload_templates()
    except (ValueError, FileNotFoundError, OSError) as exc:
        logger.error("Template reload failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Template reload failed: {exc}") from exc
    return {"reloaded": list(reloaded.keys())}


@router.post("/{ticket_id}/comments")
def post_private_comment(ticket_id: str, body: PrivateCommentRequest) -> dict:
    """Add a templated private comment to a Zoho Desk ticket."""
    try:
        rendered = template_engine.render_comment(body.comment_type, body.fields)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return add_private_comment(ticket_id, rendered)
    except TokenServiceError as exc:
        raise HTTPException(status_code=503, detail="Token service unavailable") from exc
    except ZohoAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
