"""FastAPI application for the Zoho Desk Ticket Modifications service.

Exposes versioned endpoints under ``/v1/`` with backward-compatible aliases
at the root.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.middleware import RequestLoggingMiddleware
from src.core.template_engine import get_available_types, template_count, templates_loaded
from src.core.zoho_client import check_token_service
from src.routers import comments, tickets
from src.schemas.tickets import HealthResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate config, set up logging, pre-load templates."""
    setup_logging(level=settings.log_level, fmt=settings.log_format)
    logger.info("Starting Zoho Desk Ticket Modifications service")
    logger.info("Org ID: %s | Token service: %s", settings.zoho_org_id, settings.token_service_url)

    # Pre-load templates (fail fast if YAML is broken)
    types = get_available_types()
    logger.info("Loaded %d comment template(s): %s", len(types), ", ".join(types.keys()))

    yield
    logger.info("Shutting down")


# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------

app = FastAPI(title="Zoho Desk Ticket Modifications", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — log full traceback, return generic error."""
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception", extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


# ---------------------------------------------------------------------------
# Versioned router
# ---------------------------------------------------------------------------

v1 = APIRouter(prefix="/v1", tags=["v1"])

v1.include_router(tickets.router)
v1.include_router(comments.router)


@v1.get("/healthz", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Liveness probe — is the process alive?"""
    return HealthResponse(
        status="ok",
        token_service_reachable=True,
        templates_loaded=True,
        template_count=0,
    )


@v1.get("/readyz", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Readiness probe — can the service serve requests?"""
    token_ok = check_token_service()
    tpl_ok = templates_loaded()
    tpl_count = template_count()

    status = "ok" if (token_ok and tpl_ok) else "degraded"
    return HealthResponse(
        status=status,
        token_service_reachable=token_ok,
        templates_loaded=tpl_ok,
        template_count=tpl_count,
    )


app.include_router(v1)


# ---------------------------------------------------------------------------
# Backward-compatible root aliases (hidden from OpenAPI docs)
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health_compat() -> HealthResponse:
    """Backward-compatible alias for /v1/readyz."""
    return readiness()


# ---------------------------------------------------------------------------
# Prometheus metrics (§38)
# ---------------------------------------------------------------------------
Instrumentator(
    excluded_handlers=[
        "/metrics",
        ".*/health.*",
        ".*/healthz",
        ".*/readyz",
    ],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
