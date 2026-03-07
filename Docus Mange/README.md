# සිංහල PDF සෙවුම  (Sinhala PDF Search)

**Offline full-text search tool for Sinhala & English PDF documents.**

This desktop application lets you import PDF files, automatically extract their text (including OCR for scanned documents with Sinhala script), and perform fast full-text searches across all indexed documents — entirely offline.

---

## Features

| Feature | Description |
|---|---|
| **PDF Import** | Add one or more PDF files; text is extracted automatically |
| **Sinhala OCR** | Scanned / image-based pages are processed with Tesseract OCR using the Sinhala (`sin`) + English (`eng`) language packs |
| **Full-text Search** | Type Sinhala or English keywords to search across all pages of all imported PDFs |
| **Built-in PDF Viewer** | View PDF pages inside the app with zoom controls |
| **Text Preview** | See the extracted text for the currently viewed page, with search-term highlighting |
| **Dark UI** | Modern dark theme using PyQt5 + Fusion style |
| **100 % Offline** | No internet connection required after setup |

---

## Project Structure

```
sinhala-pdf-search/
├─ main.py                  ← Entry-point
├─ requirements.txt
├─ assets/
│  ├─ app_icon.png
│  └─ sample_pdfs/
├─ data/
│  ├─ app.db                ← SQLite database (auto-created)
│  └─ index/                ← Whoosh search index (auto-created)
├─ src/
│  ├─ config.py             ← Paths, OCR settings, UI constants
│  ├─ ui/
│  │  ├─ main_window.py     ← Main application window
│  │  ├─ pdf_viewer.py      ← PDF page viewer widget
│  │  └─ dialogs.py         ← Progress, About, and helper dialogs
│  ├─ services/
│  │  ├─ pdf_reader.py      ← Text extraction with PyMuPDF
│  │  ├─ ocr_engine.py      ← Tesseract OCR wrapper
│  │  ├─ text_indexer.py    ← Whoosh indexing
│  │  └─ search_engine.py   ← Whoosh full-text search
│  ├─ db/
│  │  ├─ database.py        ← SQLAlchemy session & CRUD
│  │  └─ models.py          ← ORM models
│  └─ utils/
│     ├─ paths.py
│     ├─ logger.py
│     └─ helpers.py
└─ tests/
   ├─ test_ocr.py
   └─ test_search.py
```

---

## Prerequisites

1. **Python 3.9+**
2. **Tesseract OCR** installed and on your PATH  
   - Windows: download from <https://github.com/UB-Mannheim/tesseract/wiki>  
   - During installation, select the **Sinhala** language pack  
   - If Tesseract is not on PATH, set `TESSERACT_CMD` in `src/config.py`
3. **Sinhala font** (e.g. *Iskoola Pota*) installed on the system for proper UI rendering

---

## Installation

```bash
# 1. Clone / copy the project
cd sinhala-pdf-search

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Application

```bash
python main.py
```

The application will:  
1. Create the `data/` directory (SQLite DB + Whoosh index) on first run  
2. Open the main window  
3. Warn you if Tesseract is not found  

### Quick workflow

1. Click **➕ PDF එක් කරන්න** (Add PDF) to import a PDF  
2. Wait for indexing / OCR to finish (progress bar)  
3. Type a Sinhala or English keyword in the search box and click **සොයන්න** (Search)  
4. Double-click a result to jump to that page in the viewer  

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Configuration

Edit `src/config.py` to change:

| Setting | Default | Purpose |
|---|---|---|
| `TESSERACT_CMD` | `"tesseract"` | Path to Tesseract binary |
| `OCR_LANGUAGES` | `"sin+eng"` | Tesseract language codes |
| `MAX_SEARCH_RESULTS` | `200` | Max hits returned per query |
| `LOG_LEVEL` | `"DEBUG"` | Logging verbosity |

---

## License

Internal / Ministry use.
