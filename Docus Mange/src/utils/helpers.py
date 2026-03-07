# ──────────────────────────────────────────────────────────────
# Utility  –  Miscellaneous helpers
# ──────────────────────────────────────────────────────────────
import re
import unicodedata


def sanitise_text(text: str) -> str:
    """Normalise Unicode (decompose ligatures) and collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def highlight_matches(text: str, query: str) -> str:
    """
    Wrap every occurrence of *query* in the *text* with <b> tags
    for rich-text display in Qt.  Case-insensitive.
    """
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<b style='color:#e74c3c'>{m.group()}</b>", text)


def page_label(page_num: int) -> str:
    """Human-readable 1-based page label."""
    return f"Page {page_num + 1}"


def truncate(text: str, length: int = 300) -> str:
    """Truncate text for preview purposes."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + " …"
