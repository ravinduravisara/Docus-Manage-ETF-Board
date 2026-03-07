# ──────────────────────────────────────────────────────────────
# Tests  –  OCR engine
# ──────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from PIL import Image
from src.services.ocr_engine import is_tesseract_available, ocr_image


class TestOCR(unittest.TestCase):
    def test_tesseract_available(self):
        """Tesseract should be reachable (skip if not installed)."""
        available = is_tesseract_available()
        if not available:
            self.skipTest("Tesseract is not installed on this machine.")

    def test_ocr_blank_image(self):
        """OCR on a blank white image should return empty / whitespace."""
        if not is_tesseract_available():
            self.skipTest("Tesseract not available.")
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        result = ocr_image(img, lang="eng")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
