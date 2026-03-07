# ──────────────────────────────────────────────────────────────
# UI  –  PDF viewer widget  (renders pages via PyMuPDF)
# ──────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QSpinBox, QComboBox, QSizePolicy,
)
from PyQt5.QtGui import QImage, QPixmap, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent, QPoint
import fitz  # PyMuPDF


class PDFViewer(QWidget):
    """A widget that displays a single PDF page at a time."""

    page_changed = pyqtSignal(int)   # emits 0-based page number

    # Special sentinel values for auto-fit modes
    FIT_WIDTH = -1.0
    FIT_PAGE  = -2.0

    ZOOM_LEVELS = [FIT_WIDTH, FIT_PAGE, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
    ZOOM_LABELS = [
        "Fit Width", "Fit Page",
        "50 %", "75 %", "100 %", "125 %", "150 %", "200 %", "300 %",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc = None
        self._current_page = 0
        self._zoom = self.FIT_WIDTH          # default: auto-fit width

        self._resize_timer = QTimer(self)    # debounce resize events
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(100)
        self._resize_timer.timeout.connect(self._render)

        self._build_ui()

    # ── UI construction ─────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        tb = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Prev")
        self.btn_next = QPushButton("Next ▶")
        self.spin_page = QSpinBox()
        self.spin_page.setMinimum(1)
        self.spin_page.setPrefix("Page ")
        self.lbl_total = QLabel("/ 0")
        self.cmb_zoom = QComboBox()
        for label in self.ZOOM_LABELS:
            self.cmb_zoom.addItem(label)
        self.cmb_zoom.setCurrentIndex(0)     # "Fit Width" by default

        tb.addWidget(self.btn_prev)
        tb.addWidget(self.spin_page)
        tb.addWidget(self.lbl_total)
        tb.addWidget(self.btn_next)
        tb.addStretch()
        tb.addWidget(QLabel("Zoom:"))
        tb.addWidget(self.cmb_zoom)
        layout.addLayout(tb)

        # Scroll area with image label
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll.setWidget(self.lbl_image)
        layout.addWidget(self.scroll, 1)

        # Install event filter for mouse-wheel zoom & drag-pan
        self.scroll.viewport().installEventFilter(self)
        self._dragging = False
        self._drag_pos = QPoint()

        # Signals
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next.clicked.connect(self._next_page)
        self.spin_page.valueChanged.connect(self._on_spin)
        self.cmb_zoom.currentIndexChanged.connect(self._on_zoom)

    # ── Public API ──────────────────────────────────────────
    def load(self, path: str, page: int = 0):
        """Open a PDF and show the given page."""
        # Close any previously-open document to avoid leaking file handles
        if self._doc:
            self._doc.close()

        self._doc = fitz.open(path)
        self._current_page = max(0, min(page, len(self._doc) - 1))

        # Block signals so setMaximum / setValue don't trigger _on_spin
        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(len(self._doc))
        self.spin_page.setValue(self._current_page + 1)
        self.spin_page.blockSignals(False)

        self.lbl_total.setText(f"/ {len(self._doc)}")
        self._render()

    def go_to_page(self, page_num: int):
        """Navigate to a specific 0-based page."""
        if self._doc is None:
            return
        self._current_page = max(0, min(page_num, len(self._doc) - 1))
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(self._current_page + 1)
        self.spin_page.blockSignals(False)
        self._render()
        self.page_changed.emit(self._current_page)

    def close_doc(self):
        if self._doc:
            self._doc.close()
            self._doc = None
        self.lbl_image.clear()
        self._current_page = 0
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(1)
        self.spin_page.setMaximum(1)
        self.spin_page.blockSignals(False)
        self.lbl_total.setText("/ 0")

    @property
    def current_page(self):
        return self._current_page

    @property
    def page_count(self):
        return len(self._doc) if self._doc else 0

    # ── Internal ────────────────────────────────────────────
    def _effective_zoom(self):
        """Calculate the actual zoom factor, handling Fit Width / Fit Page."""
        if self._doc is None:
            return 1.0

        page = self._doc[self._current_page]
        page_rect = page.rect                        # unscaled page size
        pw, ph = page_rect.width, page_rect.height

        viewport = self.scroll.viewport()
        vw = viewport.width() - 2                    # small margin for scrollbar
        vh = viewport.height() - 2

        if self._zoom == self.FIT_WIDTH:
            return vw / pw if pw else 1.0
        elif self._zoom == self.FIT_PAGE:
            scale_w = vw / pw if pw else 1.0
            scale_h = vh / ph if ph else 1.0
            return min(scale_w, scale_h)
        else:
            return self._zoom

    def _render(self):
        if self._doc is None:
            return
        zoom = self._effective_zoom()
        page = self._doc[self._current_page]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        fmt = QImage.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt).copy()
        self.lbl_image.setPixmap(QPixmap.fromImage(qimg))
        self.lbl_image.adjustSize()

    def resizeEvent(self, event):
        """Re-render on resize so auto-fit modes stay accurate."""
        super().resizeEvent(event)
        if self._zoom in (self.FIT_WIDTH, self.FIT_PAGE):
            self._resize_timer.start()

    def _prev_page(self):
        if self._current_page > 0:
            self.go_to_page(self._current_page - 1)

    def _next_page(self):
        if self._doc and self._current_page < len(self._doc) - 1:
            self.go_to_page(self._current_page + 1)

    def _on_spin(self, val):
        self.go_to_page(val - 1)

    def _on_zoom(self, idx):
        self._zoom = self.ZOOM_LEVELS[idx]
        self._render()

    # ── Mouse interactions ──────────────────────────────────
    def _set_manual_zoom(self, factor):
        """Set a manual (numeric) zoom, clamping to 10 %–500 %."""
        factor = max(0.10, min(factor, 5.0))
        self._zoom = factor
        # Update combo to closest preset or clear it
        self.cmb_zoom.blockSignals(True)
        label = f"{int(round(factor * 100))} %"
        idx = self.cmb_zoom.findText(label)
        if idx >= 0:
            self.cmb_zoom.setCurrentIndex(idx)
        else:
            self.cmb_zoom.setCurrentIndex(-1)  # no preset selected
        self.cmb_zoom.blockSignals(False)
        self._render()

    def eventFilter(self, obj, event):
        """Handle Ctrl+Wheel zoom and middle/left-drag panning."""
        if obj is not self.scroll.viewport():
            return super().eventFilter(obj, event)

        etype = event.type()

        # ── Ctrl + Mouse-wheel  →  zoom ────────────────────
        if etype == QEvent.Wheel and event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta == 0:
                return True
            current = self._effective_zoom()
            step = 0.1 if abs(delta) < 200 else 0.25
            new_zoom = current + step * (1 if delta > 0 else -1)
            self._set_manual_zoom(new_zoom)
            return True   # consumed

        # ── Middle-button or Left-button drag  →  pan ──────
        if etype == QEvent.MouseButtonPress:
            if event.button() in (Qt.MiddleButton, Qt.LeftButton):
                self._dragging = True
                self._drag_pos = event.globalPos()
                self.scroll.viewport().setCursor(QCursor(Qt.ClosedHandCursor))
                return True

        if etype == QEvent.MouseMove and self._dragging:
            delta = event.globalPos() - self._drag_pos
            self._drag_pos = event.globalPos()
            h_bar = self.scroll.horizontalScrollBar()
            v_bar = self.scroll.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            return True

        if etype == QEvent.MouseButtonRelease and self._dragging:
            self._dragging = False
            self.scroll.viewport().setCursor(QCursor(Qt.OpenHandCursor))
            return True

        return super().eventFilter(obj, event)
