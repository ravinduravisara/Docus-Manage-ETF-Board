# ──────────────────────────────────────────────────────────────
# UI  –  Dialogs  (progress, about, OCR status)
# ──────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QMessageBox, QTextEdit,
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QInputDialog,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

import os
from src.config import APP_NAME, APP_VERSION, APP_ICON
from src.db.database import get_all_categories, add_category, authenticate_admin


# ── Login dialog ────────────────────────────────────────
class LoginDialog(QDialog):
    """Admin login dialog shown at application startup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setFixedSize(380, 260)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowContextHelpButtonHint
        )
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QIcon(APP_ICON))

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel(f"<h2 style='color:#5dade2;'>🔐 {APP_NAME}</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Username")
        form.addRow("Username:", self.txt_username)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Password")
        self.txt_password.setEchoMode(QLineEdit.Password)
        form.addRow("Password:", self.txt_password)

        layout.addLayout(form)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_error)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_login = QPushButton("Login")
        self.btn_login.setDefault(True)
        self.btn_login.setFixedWidth(100)
        self.btn_login.clicked.connect(self._on_login)
        btn_row.addWidget(self.btn_login)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Focus username field
        self.txt_username.setFocus()

    def _on_login(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text()

        if not username or not password:
            self.lbl_error.setText("Please enter username and password.")
            return

        if authenticate_admin(username, password):
            self.accept()
        else:
            self.lbl_error.setText("Invalid username or password.")
            self.txt_password.selectAll()
            self.txt_password.setFocus()


# ── PDF metadata form dialog ────────────────────────────────
class PDFMetadataDialog(QDialog):
    """Form to capture Circular No., Name, Date, and Category when adding a PDF."""

    ADD_NEW_LABEL = "+ Add New Category..."

    def __init__(self, file_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Details")
        self.setMinimumWidth(460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        # Header
        layout.addWidget(QLabel(
            f"<b>Enter details for:</b> {file_name}"
        ))

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_doc_type = QComboBox()
        self.cmb_doc_type.addItems(["Circular", "Circular Letter"])
        form.addRow("Type:", self.cmb_doc_type)

        self.txt_circular_no = QLineEdit()
        self.txt_circular_no.setPlaceholderText("e.g. 01/2026")
        form.addRow("Circular No.:", self.txt_circular_no)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Document title / name")
        form.addRow("Name:", self.txt_name)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Date:", self.date_edit)

        self.cmb_category = QComboBox()
        self._load_categories()
        self.cmb_category.currentTextChanged.connect(self._on_category_changed)
        form.addRow("Category:", self.cmb_category)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_ok = QPushButton("Save && Add")
        self.btn_cancel = QPushButton("Cancel")
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    # ── Category helpers ────────────────────────────────────
    def _load_categories(self):
        """Populate the dropdown from the database."""
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("-- Select --")
        for cat in get_all_categories():
            self.cmb_category.addItem(cat)
        self.cmb_category.addItem(self.ADD_NEW_LABEL)
        self.cmb_category.blockSignals(False)

    def _on_category_changed(self, text: str):
        """When '+ Add New Category...' is selected, prompt for a name."""
        if text != self.ADD_NEW_LABEL:
            return
        name, ok = QInputDialog.getText(
            self, "New Category", "Enter category name:"
        )
        if ok and name.strip():
            added = add_category(name.strip())
            self._load_categories()
            if added:
                idx = self.cmb_category.findText(name.strip())
                if idx >= 0:
                    self.cmb_category.setCurrentIndex(idx)
            else:
                # Already exists — just select it
                idx = self.cmb_category.findText(name.strip())
                if idx >= 0:
                    self.cmb_category.setCurrentIndex(idx)
        else:
            # Cancelled — reset to "-- Select --"
            self.cmb_category.setCurrentIndex(0)

    # ── Accessors ───────────────────────────────────────────
    @property
    def doc_type(self) -> str:
        return self.cmb_doc_type.currentText()

    @property
    def circular_no(self) -> str:
        return self.txt_circular_no.text().strip()

    @property
    def doc_name(self) -> str:
        return self.txt_name.text().strip()

    @property
    def doc_date(self) -> str:
        return self.date_edit.date().toString("yyyy-MM-dd")

    @property
    def category(self) -> str:
        val = self.cmb_category.currentText()
        return "" if val == "-- Select --" else val


# ── Category Manager dialog ─────────────────────────────────
class CategoryManagerDialog(QDialog):
    """Window to view, add, edit, and delete categories."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setMinimumSize(450, 400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)

        # Header
        layout.addWidget(QLabel("<b>Categories</b>"))

        # List
        from PyQt5.QtWidgets import QListWidget
        self.lst = QListWidget()
        self.lst.setAlternatingRowColors(True)
        layout.addWidget(self.lst)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet(
            "QPushButton { background-color: #8b3a3a; }"
            "QPushButton:hover { background-color: #a04545; }"
        )
        self.btn_close = QPushButton("Close")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        # Connections
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_close.clicked.connect(self.accept)

        self._refresh()

    def _refresh(self):
        self.lst.clear()
        for cat in get_all_categories():
            self.lst.addItem(cat)
        self.btn_edit.setEnabled(self.lst.count() > 0)
        self.btn_delete.setEnabled(self.lst.count() > 0)

    def _on_add(self):
        name, ok = QInputDialog.getText(
            self, "Add Category", "Enter new category name:"
        )
        if ok and name.strip():
            if add_category(name.strip()):
                self._refresh()
            else:
                QMessageBox.information(
                    self, "Already Exists",
                    f"Category '{name.strip()}' already exists.",
                )

    def _on_edit(self):
        item = self.lst.currentItem()
        if not item:
            QMessageBox.information(self, "Select", "Select a category first.")
            return
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, "Edit Category",
            f"Rename '{old_name}' to:",
        )
        if ok and new_name.strip():
            from src.db.database import update_category
            if update_category(old_name, new_name.strip()):
                self._refresh()
            else:
                QMessageBox.warning(
                    self, "Rename Failed",
                    "Could not rename. The name may already exist.",
                )

    def _on_delete(self):
        item = self.lst.currentItem()
        if not item:
            QMessageBox.information(self, "Select", "Select a category first.")
            return
        name = item.text()
        r = QMessageBox.question(
            self, "Delete Category",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            from src.db.database import delete_category
            if delete_category(name):
                self._refresh()


# ── Progress dialog (used during indexing / OCR) ────────────
class ProgressDialog(QDialog):
    def __init__(self, title: str = "Processing...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        self.lbl_status = QLabel("Starting...")
        layout.addWidget(self.lbl_status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.btn_cancel = QPushButton("Cancel")
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignRight)

        self._cancelled = False
        self.btn_cancel.clicked.connect(self._on_cancel)

    def set_progress(self, value: int, status: str = ""):
        self.progress.setValue(value)
        if status:
            self.lbl_status.setText(status)

    def _on_cancel(self):
        self._cancelled = True
        self.close()

    @property
    def cancelled(self):
        return self._cancelled


# ── About dialog ────────────────────────────────────────────
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(400, 260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            "<p>Designed by Ravindu Ravisara</p>"
            "HR Document Management System.</p>"
            "<hr>"
            "<p><small>PyQt5 · PyMuPDF · Tesseract OCR · Whoosh</small></p>"
        ))
        btn = QPushButton("OK")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignRight)


# ── Page-text preview dialog ───────────────────────────────
class TextPreviewDialog(QDialog):
    """Shows the extracted text for a page."""
    def __init__(self, text: str, page_label: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Text – {page_label}")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(text)
        layout.addWidget(te)
        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignRight)


# ── Convenience wrappers ────────────────────────────────────
def info_box(parent, title, msg):
    QMessageBox.information(parent, title, msg)

def warn_box(parent, title, msg):
    QMessageBox.warning(parent, title, msg)

def error_box(parent, title, msg):
    QMessageBox.critical(parent, title, msg)

def confirm_box(parent, title, msg) -> bool:
    r = QMessageBox.question(parent, title, msg,
                             QMessageBox.Yes | QMessageBox.No)
    return r == QMessageBox.Yes
