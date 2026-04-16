# Zoho Desk Ticket Modifier

FastAPI microservice for updating Zoho Desk ticket fields and adding templated private comments.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `PATCH` | `/v1/tickets/{id}` | Update a ticket field |
| `POST` | `/v1/tickets/{id}/comments` | Add a templated private comment |
| `GET` | `/v1/tickets/comment-types` | List available comment types and required fields |
| `POST` | `/v1/tickets/comment-types/reload` | Hot-reload templates from YAML |
| `GET` | `/v1/healthz` | Liveness probe |
| `GET` | `/v1/readyz` | Readiness probe (checks token service + templates) |

## Comment Types

Defined in `comment_templates.yaml` (editable without code changes):

- **text_message** - Text message sent notification
- **robot_call** - Robot call made notification
- **instant_message** - Instant message sent notification
- **desktop_notification** - Desktop notification sent
- **live_call** - Live call request notification

Each comment includes an auto-generated UTC timestamp.

## Local Development

```bash
# Prerequisites: Zoho token service running on port 8000

# Install dependencies
uv sync

# Create .env from template
cp .env.example .env
# Edit .env and set ZOHO_ORG_ID

# Run
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1

# Swagger docs at http://localhost:8001/docs
```

## Configuration

All settings are loaded from `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKEN_SERVICE_URL` | `http://localhost:8000/v1/token` | Zoho token service URL |
| `ZOHO_DESK_BASE_URL` | `https://desk.zoho.com/api/v1` | Zoho Desk API base URL |
| `ZOHO_ORG_ID` | *(required)* | Zoho organization ID |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | `json` for production, `text` for local dev |
| `ZOHO_REQUEST_TIMEOUT` | `30` | Zoho API timeout (seconds) |
| `TOKEN_REQUEST_TIMEOUT` | `10` | Token service timeout (seconds) |

## Deployment

Deployed via GitHub Actions CI/CD to EC2. Push to `main` triggers: test, build (GHCR), deploy.

Changes to `*.md`, `LICENSE`, `.gitignore`, or `credentials/` do **not** trigger a rebuild.

`.env` and `comment_templates.yaml` are bind-mounted from the host and persist across container rebuilds.
