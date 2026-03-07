# ──────────────────────────────────────────────────────────────
# Sinhala PDF Search  –  Application-wide configuration
# ──────────────────────────────────────────────────────────────
import os
import sys

# ── Paths ────────────────────────────────────────────────────
# When frozen by PyInstaller, resolve paths relative to the exe location.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    # Bundled read-only assets live inside the temp _MEIPASS folder
    BUNDLE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = BASE_DIR
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")
DB_PATH = os.path.join(DATA_DIR, "app.db")
ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")
APP_ICON = os.path.join(ASSETS_DIR, "app_icon.png")

# ── Tesseract OCR ───────────────────────────────────────────
# If Tesseract is not on PATH, set the full path here.
TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Language code(s) for Tesseract – "sin" is Sinhala, "eng" is English
OCR_LANGUAGES = "sin+eng"

# ── Search / Indexing ───────────────────────────────────────
# Minimum word length to index
MIN_WORD_LENGTH = 1

# Maximum search results returned
MAX_SEARCH_RESULTS = 200

# ── UI ──────────────────────────────────────────────────────
APP_NAME = "Docus Manage"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL = "DEBUG"
LOG_FILE = os.path.join(DATA_DIR, "app.log")
