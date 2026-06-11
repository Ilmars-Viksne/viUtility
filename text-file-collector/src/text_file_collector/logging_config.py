"""Centralized logging configuration."""

from __future__ import annotations

import logging


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    normalized_level = log_level.upper()
    level = getattr(logging, normalized_level, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
