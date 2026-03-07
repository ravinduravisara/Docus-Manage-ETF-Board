# ──────────────────────────────────────────────────────────────
# Utility  –  Application logger
# ──────────────────────────────────────────────────────────────
import logging
import os
from src.config import LOG_LEVEL, LOG_FILE, DATA_DIR


def get_logger(name: str = "sinhala_pdf_search") -> logging.Logger:
    """Return a configured logger that writes to console AND file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File
    os.makedirs(DATA_DIR, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
