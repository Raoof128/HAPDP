"""Audit logging utilities."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from config import load_settings


def _configure_logger(log_path: Optional[Path]) -> logging.Logger:
    logger = logging.getLogger("privacy_proxy.audit")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_audit_logger() -> logging.Logger:
    settings = load_settings()
    return _configure_logger(settings.audit_log_path)


def reset_audit_logger() -> None:
    """Remove handlers so tests can reconfigure log destinations."""

    logger = logging.getLogger("privacy_proxy.audit")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def emit_audit_event(
    request_id: str,
    resource_type: str,
    client_host: str,
    modifications: Iterable[str],
    status: str,
) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "resource_type": resource_type,
        "client_host": client_host,
        "status": status,
        "modified_fields": list(modifications),
    }
    logger = get_audit_logger()
    logger.info(json.dumps(payload))
