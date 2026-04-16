"""Application settings loaded from environment variables and .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    token_service_url: str = "http://localhost:8000/v1/token"
    zoho_desk_base_url: str = "https://desk.zoho.com/api/v1"
    zoho_org_id: str

    comment_templates_path: str = str(PROJECT_ROOT / "comment_templates.yaml")

    log_level: str = "INFO"
    log_format: str = "json"

    zoho_request_timeout: int = 30
    token_request_timeout: int = 10

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
