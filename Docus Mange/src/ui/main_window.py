# ──────────────────────────────────────────────────────────────
# UI  –  Main application window
# ──────────────────────────────────────────────────────────────
import os
import shutil
import subprocess

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QAction, QStatusBar, QToolBar, QComboBox,
    QApplication, QStyledItemDelegate,
    QSplitter, QFrame,
)
from PyQt5.QtGui import QIcon, QTextDocument
from PyQt5.QtCore import Qt, QSize

from src.config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, APP_ICON,
)
from src.db.database import (
    add_document, get_all_documents,
    delete_document, get_document_by_path,
)
from src.services.pdf_reader import get_page_count
from src.services.ocr_engine import is_tesseract_available
from src.utils.logger import get_logger
from src.ui.pdf_viewer import PDFViewer
from src.ui.dialogs import (
    AboutDialog, PDFMetadataDialog,
    CategoryManagerDialog,
    info_box, warn_box, error_box, confirm_box,
)

log = get_logger(__name__)


# ═════════════════════════════════════════════════════════════
# Delegate for rendering HTML in QListWidget items
# ═════════════════════════════════════════════════════════════
class HtmlDelegate(QStyledItemDelegate):
    """Renders list items using rich HTML stored in UserRole+2."""

    def paint(self, painter, option, index):
        # Draw selection / hover background
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawPrimitive(style.PE_PanelItemViewItem, option, painter, option.widget)

        html = index.data(Qt.UserRole + 2)
        if not html:
            super().paint(painter, option, index)
            return

        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width() - 8)

        painter.save()
        painter.translate(option.rect.left() + 4, option.rect.top() + 2)
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        html = index.data(Qt.UserRole + 2)
        if not html:
            return super().sizeHint(option, index)
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width() - 8 if option.rect.width() > 0 else 250)
        return QSize(int(doc.idealWidth()) + 8, max(int(doc.size().height()) + 4, 52))


# ═════════════════════════════════════════════════════════════
# Main window
# ═════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QIcon(APP_ICON))

        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._refresh_doc_list()

    def showEvent(self, event):
        """Run deferred checks after the window is first shown."""
        super().showEvent(event)
        if not hasattr(self, '_tesseract_checked'):
            self._tesseract_checked = True
            self._check_tesseract()

    # ── Menu ────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("File (&F)")
        act_open = QAction("Add PDF...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._add_pdf)
        file_menu.addAction(act_open)

        act_cat = QAction("Manage Categories...", self)
        act_cat.triggered.connect(self._open_category_manager)
        file_menu.addAction(act_cat)

        file_menu.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        help_menu = mb.addMenu("Help (&H)")
        act_about = QAction("About...", self)
        act_about.triggered.connect(lambda: AboutDialog(self).exec_())
        help_menu.addAction(act_about)

    def _open_category_manager(self):
        """Open the Category Manager window."""
        CategoryManagerDialog(parent=self).exec_()

    # ── Toolbar (with integrated search bar) ──────────────────
    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setIconSize(QSize(24, 24))
        tb.setMovable(False)
        self.addToolBar(tb)

        btn_add = QPushButton("➕ Add PDF")
        btn_add.clicked.connect(self._add_pdf)
        tb.addWidget(btn_add)

        btn_del = QPushButton("🗑  Remove")
        btn_del.clicked.connect(self._remove_pdf)
        tb.addWidget(btn_del)

        btn_download = QPushButton("📥 Download")
        btn_download.clicked.connect(self._download_pdf)
        tb.addWidget(btn_download)

        btn_print = QPushButton("🖨  Print")
        btn_print.clicked.connect(self._print_pdf)
        tb.addWidget(btn_print)

    # ── Central widget (splitter: doc list + PDF viewer) ───
    def _build_central(self):
        # Left panel — document list
        left_panel = QFrame(self)
        left_panel.setFrameShape(QFrame.NoFrame)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)

        # Panel header
        header = QLabel("<b>PDF Documents</b>")
        header.setStyleSheet("color:#e0e0e0; font-size:14px; padding:4px 0;")
        left_layout.addWidget(header)

        # Type filter
        self.cmb_type_filter = QComboBox()
        self.cmb_type_filter.addItems(["All", "Circular", "Circular Letter"])
        self.cmb_type_filter.currentIndexChanged.connect(self._filter_doc_list)
        left_layout.addWidget(self.cmb_type_filter)

        # Text filter
        filter_row = QHBoxLayout()
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Filter documents...")
        self.txt_filter.textChanged.connect(self._filter_doc_list)
        self.btn_clear_filter = QPushButton("✕")
        self.btn_clear_filter.setFixedWidth(30)
        self.btn_clear_filter.setToolTip("Clear filter")
        self.btn_clear_filter.clicked.connect(lambda: self.txt_filter.clear())
        filter_row.addWidget(self.txt_filter)
        filter_row.addWidget(self.btn_clear_filter)
        left_layout.addLayout(filter_row)

        self.lst_docs = QListWidget()
        self.lst_docs.setItemDelegate(HtmlDelegate(self.lst_docs))
        self.lst_docs.currentRowChanged.connect(self._on_doc_selected)
        left_layout.addWidget(self.lst_docs)

        # Right panel — PDF viewer
        self.viewer = PDFViewer()

        # Splitter
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.viewer)
        splitter.setStretchFactor(0, 0)  # doc list: fixed
        splitter.setStretchFactor(1, 1)  # viewer: stretches
        splitter.setSizes([320, 900])    # initial widths
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:hover {
                background-color: #4a8ab5;
            }
        """)

        self.setCentralWidget(splitter)

    # ── Status bar ──────────────────────────────────────────
    def _build_statusbar(self):
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage("Ready.")

    # ── Tesseract check ─────────────────────────────────────
    def _check_tesseract(self):
        if not is_tesseract_available():
            self.sb.showMessage(
                "⚠ Tesseract OCR not found – OCR disabled. "
                "Install Tesseract or set TESSERACT_CMD in config."
            )

    # ══════════════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════════════

    def _add_pdf(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not paths:
            return
        for p in paths:
            p = os.path.normpath(p)
            if get_document_by_path(p):
                info_box(self, "Already Added", f"This PDF has already been added:\n{p}")
                continue

            # Show metadata form
            fname = os.path.basename(p)
            dlg = PDFMetadataDialog(file_name=fname, parent=self)
            if dlg.exec_() != dlg.Accepted:
                continue  # user cancelled

            try:
                total = get_page_count(p)
            except Exception as exc:
                log.error("Failed to read PDF '%s': %s", p, exc)
                error_box(self, "Invalid PDF",
                          f"Could not read the PDF file:\n{p}\n\n{exc}")
                continue

            try:
                add_document(
                    p, fname, total,
                    circular_no=dlg.circular_no,
                    doc_type=dlg.doc_type,
                    doc_name=dlg.doc_name,
                    doc_date=dlg.doc_date,
                    category=dlg.category,
                )
            except Exception as exc:
                log.error("Failed to save document '%s': %s", p, exc)
                error_box(self, "Database Error",
                          f"Could not save the document:\n{p}\n\n{exc}")
                continue

        self._refresh_doc_list()



    def _get_selected_doc(self):
        """Return the currently selected PDFDocument or None."""
        row = self.lst_docs.currentRow()
        if row < 0:
            return None
        item = self.lst_docs.item(row)
        if item is None:
            return None
        orig_idx = item.data(Qt.UserRole + 1)
        if orig_idx is None or orig_idx >= len(self._doc_objects):
            return None
        return self._doc_objects[orig_idx]

    def _download_pdf(self):
        """Save a copy of the selected PDF to a user-chosen location."""
        doc = self._get_selected_doc()
        if not doc:
            warn_box(self, "No Selection", "Please select a document first.")
            return
        if not os.path.exists(doc.file_path):
            warn_box(self, "File Not Found",
                     f"The source file no longer exists:\n{doc.file_path}")
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", doc.file_name,
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not dest:
            return
        try:
            shutil.copy2(doc.file_path, dest)
            self.sb.showMessage(f"Saved to: {dest}")
            info_box(self, "Download Complete", f"PDF saved to:\n{dest}")
        except Exception as exc:
            log.error("Failed to copy PDF: %s", exc)
            error_box(self, "Download Failed", f"Could not save the file:\n{exc}")

    def _print_pdf(self):
        """Send the selected PDF to the default printer via the OS."""
        doc = self._get_selected_doc()
        if not doc:
            warn_box(self, "No Selection", "Please select a document first.")
            return
        if not os.path.exists(doc.file_path):
            warn_box(self, "File Not Found",
                     f"The source file no longer exists:\n{doc.file_path}")
            return
        try:
            os.startfile(doc.file_path, "print")
            self.sb.showMessage(f"Sent to printer: {doc.file_name}")
        except Exception as exc:
            log.error("Print failed: %s", exc)
            error_box(self, "Print Failed",
                      f"Could not print the file:\n{exc}")

    def _remove_pdf(self):
        row = self.lst_docs.currentRow()
        if row < 0:
            return
        item = self.lst_docs.item(row)
        if item is None:
            return
        orig_idx = item.data(Qt.UserRole + 1)
        if orig_idx is None or orig_idx >= len(self._doc_objects):
            return
        doc = self._doc_objects[orig_idx]
        if not confirm_box(self, "Remove",
                           f"Remove '{doc.file_name}'?"):
            return
        delete_document(doc.id)
        self.viewer.close_doc()
        self._refresh_doc_list()
        self.sb.showMessage("Document removed.")

    # ── Document list ───────────────────────────────────────
    def _refresh_doc_list(self):
        self.lst_docs.clear()
        self._doc_objects = get_all_documents()
        filter_text = self.txt_filter.text().strip().lower()
        type_filter = self.cmb_type_filter.currentText()
        for i, doc in enumerate(self._doc_objects):
            circ = doc.circular_no or "-"
            doc_type = getattr(doc, 'doc_type', '') or "Circular"
            name = doc.doc_name or doc.file_name
            date = doc.doc_date or "-"
            cat = doc.category or "-"
            pages = doc.total_pages

            # Type filter
            if type_filter != "All" and doc_type != type_filter:
                continue

            # Text filter
            if filter_text:
                searchable = f"{circ} {doc_type} {name} {date} {cat}".lower()
                if filter_text not in searchable:
                    continue

            html = (
                f"<div style='padding:2px 0;'>"
                f"<b style='color:#5dade2;font-size:13px;'>{doc_type}: {circ}</b>"
                f"<br/>"
                f"<span style='color:#e0e0e0;font-size:12px;'>{name}</span>"
                f"<br/>"
                f"<span style='color:#aaa;font-size:11px;'>"
                f"Date: {date}  &nbsp;|&nbsp;  Category: {cat}  &nbsp;|&nbsp;  {pages} pages"
                f"</span>"
                f"</div>"
            )
            item = QListWidgetItem()
            item.setData(Qt.UserRole + 1, i)   # original index
            item.setData(Qt.DisplayRole, "")
            item.setData(Qt.UserRole + 2, html)
            item.setSizeHint(QSize(0, 62))
            self.lst_docs.addItem(item)

    def _filter_doc_list(self, _text: str = ""):
        """Re-filter the document list when filter text changes."""
        self._refresh_doc_list()

    def _on_doc_selected(self, row):
        if row < 0:
            return
        item = self.lst_docs.item(row)
        if item is None:
            return
        orig_idx = item.data(Qt.UserRole + 1)
        if orig_idx is None or orig_idx >= len(self._doc_objects):
            return
        doc = self._doc_objects[orig_idx]
        if not os.path.exists(doc.file_path):
            warn_box(self, "File Not Found",
                     f"The file no longer exists:\n{doc.file_path}")
            return
        self.viewer.load(doc.file_path)
        self.sb.showMessage(f"Opened: {doc.file_name}")
