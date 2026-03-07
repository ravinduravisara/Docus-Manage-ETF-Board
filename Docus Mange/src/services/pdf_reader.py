# ──────────────────────────────────────────────────────────────
# Service  –  PDF reader  (text extraction via PyMuPDF)
# ──────────────────────────────────────────────────────────────
from typing import List, Dict
import fitz  # PyMuPDF

from src.utils.helpers import sanitise_text
from src.utils.logger import get_logger

log = get_logger(__name__)


def open_pdf(path: str) -> fitz.Document:
    """Open and return a PyMuPDF Document handle."""
    doc = fitz.open(path)
    log.info("Opened PDF: %s  (%d pages)", path, len(doc))
    return doc


def extract_text_from_page(doc: fitz.Document, page_num: int) -> str:
    """Extract embedded text from a single page (0-based)."""
    page = doc[page_num]
    raw = page.get_text("text")
    return sanitise_text(raw)


def extract_all_text(path: str) -> List[Dict]:
    """
    Return a list of dicts:
      [{"page_number": 0, "text": "...", "has_text": True/False}, ...]
    """
    doc = open_pdf(path)
    results = []
    for i in range(len(doc)):
        text = extract_text_from_page(doc, i)
        results.append({
            "page_number": i,
            "text": text,
            "has_text": bool(text.strip()),
        })
    doc.close()
    return results


def get_page_count(path: str) -> int:
    doc = fitz.open(path)
    n = len(doc)
    doc.close()
    return n


def render_page_pixmap(path: str, page_num: int,
                       zoom: float = 2.0) -> fitz.Pixmap:
    """Render a page to a Pixmap for display / OCR."""
    doc = fitz.open(path)
    page = doc[page_num]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    doc.close()
    return pix
