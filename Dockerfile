# Production image for the modify-Zoho-Desk-ticket FastAPI microservice.
# Uses `uv` to install from pyproject.toml + uv.lock so dep drift is
# impossible. CMD wraps `uvicorn` with `opentelemetry-instrument`; traces
# ship via OTLP when OTEL_* env vars are set by docker-compose.

FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Dependency layer — cached unless pyproject.toml / uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# OTel auto-instrumentors (fastapi, httpx, logging, asgi, stdlib).
RUN opentelemetry-bootstrap -a install

# Source + runtime templates.
COPY main.py .
COPY src/ src/
COPY comment_templates.yaml .

EXPOSE 8001

# opentelemetry-instrument wraps uvicorn. Inert when OTEL env vars absent.
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
