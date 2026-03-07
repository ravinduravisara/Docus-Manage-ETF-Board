# ──────────────────────────────────────────────────────────────
# Utility  –  Path helpers
# ──────────────────────────────────────────────────────────────
import os
from src.config import DATA_DIR, INDEX_DIR


def ensure_dirs():
    """Create required data directories if they don't exist."""
    for d in (DATA_DIR, INDEX_DIR):
        os.makedirs(d, exist_ok=True)


def normalise_path(path: str) -> str:
    """Return a canonical, absolute version of *path*."""
    return os.path.normpath(os.path.abspath(path))


def short_name(path: str, max_len: int = 60) -> str:
    """Return a display-friendly truncated filename."""
    name = os.path.basename(path)
    if len(name) > max_len:
        return name[: max_len - 3] + "..."
    return name
