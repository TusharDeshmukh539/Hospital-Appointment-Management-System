import json
import logging
from datetime import datetime, timezone

# One logger used for all audit events.
audit_logger = logging.getLogger("hospital.audit")
# One logger for technical errors.
app_logger = logging.getLogger("hospital.app")


class JsonFormatter(logging.Formatter):
    """Turns a log record into a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # audit_log() puts its extra fields in record.audit
        extra_fields = getattr(record, "audit", None)
        if extra_fields:
            data.update(extra_fields)
        return json.dumps(data, default=str)


def setup_logging() -> None:
    """Attach a console handler with the JSON formatter (called once at startup)."""
    root_logger = logging.getLogger("hospital")
    if root_logger.handlers:  # already configured (avoids duplicate lines)
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def audit_log(action: str, user_id: int | None = None, **details) -> None:
    """Write one audit line.

    Example: audit_log("appointment.book", user_id=5, appointment_id=12)
    Only pass ids and harmless values in **details!
    """
    audit_logger.info(action, extra={"audit": {"action": action, "user_id": user_id, **details}})
