import logging
import os
from typing import Optional

_LOGGING_INITIALIZED = False


def _ensure_logging_configured() -> None:
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return
    level_name = os.getenv("TP_API_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    _LOGGING_INITIALIZED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    _ensure_logging_configured()
    return logging.getLogger(name or "tp_api")
