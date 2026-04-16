"""Pydantic request/response models for the ticket modification API."""

from typing import Any

from pydantic import BaseModel, Field


class UpdateFieldRequest(BaseModel):
    """Request body for updating a single field on a Zoho Desk ticket."""

    field_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Zoho Desk ticket field name",
        examples=["subject", "status", "priority"],
    )
    value: Any = Field(
        ...,
        description="New value for the field (string, number, boolean, or object)",
    )


class PrivateCommentRequest(BaseModel):
    """Request body for adding a templated private comment to a ticket."""

    comment_type: str = Field(
        ...,
        min_length=1,
        description="Comment template key from comment_templates.yaml",
        examples=["text_message", "robot_call", "instant_message", "desktop_notification", "live_call"],
    )
    fields: dict[str, str] = Field(
        ...,
        description="Template placeholder values keyed by field name",
        examples=[{"recipient_name": "Dr. Smith", "phone_number": "+1-555-0100", "message": "Code Stroke activated"}],
    )


class CommentTypeInfo(BaseModel):
    """Schema for a single comment type returned by the list endpoint."""

    label: str = Field(..., description="Human-readable name", examples=["Text Message Sent"])
    fields: list[str] = Field(..., description="Required placeholder names", examples=[["recipient_name", "phone_number", "message"]])


class HealthResponse(BaseModel):
    """Response from health check endpoints."""

    status: str = Field(..., description="Service status: 'ok' or 'degraded'", examples=["ok"])
    token_service_reachable: bool = Field(..., description="Whether the token service responded successfully")
    templates_loaded: bool = Field(..., description="Whether comment templates are loaded")
    template_count: int = Field(0, description="Number of loaded comment template types")


class ErrorResponse(BaseModel):
    """Standard error envelope for non-2xx responses."""

    detail: str = Field(..., description="Human-readable error message")
    request_id: str | None = Field(None, description="Correlation ID for tracing")
