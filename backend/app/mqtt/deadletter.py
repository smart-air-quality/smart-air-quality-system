"""Log malformed MQTT payloads for inspection (file append or stderr)."""

import json
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)


def log_rejected(reason: str, raw: bytes | None = None, detail: str | None = None) -> None:
    """Structured dead-letter line: JSON one object per line."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "detail": detail,
        "payload_preview": (raw[:512].decode("utf-8", errors="replace") if raw else None),
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    path = settings.mqtt_dead_letter_path
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            logger.error("dead_letter file write failed: %s", e)
    logger.warning("MQTT ingest rejected: %s %s", reason, detail or "")
