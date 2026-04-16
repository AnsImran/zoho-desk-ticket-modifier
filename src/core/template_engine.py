"""Comment template loader and renderer.

Loads comment type definitions from a YAML file and renders them with
caller-supplied field values and an auto-injected UTC timestamp.
"""

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.core.config import settings

logger = logging.getLogger(__name__)

_templates: dict | None = None
_lock = threading.Lock()


def _validate_template(key: str, tpl: dict) -> None:
    """Raise ValueError if a template entry is missing required keys."""
    for required in ("label", "fields", "template"):
        if required not in tpl:
            raise ValueError(f"Template '{key}' is missing required key '{required}'")
    if not isinstance(tpl["fields"], list):
        raise ValueError(f"Template '{key}': 'fields' must be a list")


def _load_templates() -> dict:
    global _templates
    with _lock:
        if _templates is None:
            path = Path(settings.comment_templates_path)
            logger.info("Loading comment templates from %s", path)
            with open(path) as f:
                data = yaml.safe_load(f)

            types = data.get("comment_types")
            if not types:
                raise ValueError(f"No 'comment_types' found in {path}")

            for key, tpl in types.items():
                _validate_template(key, tpl)

            _templates = types
            logger.info("Loaded %d comment template(s): %s", len(_templates), ", ".join(_templates.keys()))
        return _templates


def reload_templates() -> dict:
    """Force-reload templates from disk. Validates before replacing."""
    global _templates
    with _lock:
        _templates = None
    loaded = _load_templates()
    logger.info("Templates reloaded successfully")
    return loaded


def get_available_types() -> dict:
    templates = _load_templates()
    return {
        key: {"label": t["label"], "fields": t["fields"]}
        for key, t in templates.items()
    }


def templates_loaded() -> bool:
    """Check if templates are currently loaded. Used by readiness probe."""
    return _templates is not None


def template_count() -> int:
    """Return the number of loaded templates, or 0 if not loaded."""
    return len(_templates) if _templates is not None else 0


def render_comment(comment_type: str, field_values: dict) -> str:
    """Render a comment template with the given field values."""
    templates = _load_templates()

    if comment_type not in templates:
        available = ", ".join(templates.keys())
        raise ValueError(f"Unknown comment type '{comment_type}'. Available: {available}")

    tpl = templates[comment_type]

    missing = [f for f in tpl["fields"] if f not in field_values]
    if missing:
        raise ValueError(f"Missing required fields for '{comment_type}': {missing}")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    rendered = tpl["template"].format(timestamp_utc=timestamp, **field_values)
    logger.info("Rendered '%s' comment for ticket", comment_type)
    return rendered
