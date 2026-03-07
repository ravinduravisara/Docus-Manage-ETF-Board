# ──────────────────────────────────────────────────────────────
# Service  –  OCR engine  (Tesseract via pytesseract)
# ──────────────────────────────────────────────────────────────
import io
from typing import Optional

from PIL import Image
import pytesseract

from src.config import TESSERACT_CMD, OCR_LANGUAGES
from src.utils.helpers import sanitise_text
from src.utils.logger import get_logger

log = get_logger(__name__)

# Point pytesseract at the Tesseract binary
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def ocr_image(image: Image.Image,
              lang: str = OCR_LANGUAGES) -> str:
    """Run Tesseract OCR on a PIL Image and return cleaned text."""
    try:
        raw = pytesseract.image_to_string(image, lang=lang)
        return sanitise_text(raw)
    except Exception as e:
        log.error("OCR failed: %s", e)
        return ""


def ocr_from_pixmap(pixmap, lang: str = OCR_LANGUAGES) -> str:
    """
    Accept a PyMuPDF Pixmap, convert to PIL Image, then OCR.
    """
    img_data = pixmap.tobytes("png")
    image = Image.open(io.BytesIO(img_data))
    return ocr_image(image, lang=lang)


def ocr_pdf_page(pdf_path: str, page_num: int,
                 zoom: float = 2.0,
                 lang: str = OCR_LANGUAGES) -> str:
    """Render a PDF page and run OCR on it."""
    from src.services.pdf_reader import render_page_pixmap
    pix = render_page_pixmap(pdf_path, page_num, zoom=zoom)
    return ocr_from_pixmap(pix, lang=lang)


def is_tesseract_available() -> bool:
    """Check whether Tesseract is reachable."""
    try:
        ver = pytesseract.get_tesseract_version()
        log.info("Tesseract version: %s", ver)
        return True
    except Exception:
        log.warning("Tesseract not found – OCR will be unavailable.")
        return False


def available_languages() -> Optional[list]:
    """Return the list of Tesseract language packs installed."""
    try:
        return pytesseract.get_languages(config="")
    except Exception:
        return None
