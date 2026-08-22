import logging
import json
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Optional

# Context variable to hold the current request ID across async tasks
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# Sensitive keys that must be redacted from logs
SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "authorization", "secret", "secret_key", "secret_ref", "api_key"
}


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx_var.get() or getattr(record, "request_id", None),
        }

        user_id = user_id_ctx_var.get() or getattr(record, "user_id", None)
        if user_id:
            log_obj["user_id"] = user_id

        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure root logger with structured JSON or human-readable format."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s] %(message)s (req_id=%(request_id)s)",
                defaults={"request_id": None},
            )
        )

    root_logger.addHandler(console_handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("phantom")
