from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.handlers.clear()
    root.addHandler(handler)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Merge extra dict if provided under record.extra
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            # Mask sensitive fields just in case
            for key in list(extra.keys()):
                if key.lower() in {"token", "password", "api_hash", "code", "2fa", "session"}:
                    extra[key] = "***"
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def json_log(logger: logging.Logger, level: int, message: str, **fields: Any) -> None:
    logger.log(level, message, extra={"extra": fields})
