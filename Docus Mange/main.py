#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────
# Sinhala PDF Search  –  Application entry-point
# ──────────────────────────────────────────────────────────────
"""
Offline full-text search tool for Sinhala & English PDF documents.

Usage:
    python main.py
"""
import sys
import os
import multiprocessing

# Ensure the project root is on sys.path so `src.*` imports work
# regardless of the working directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from src.utils.paths import ensure_dirs
from src.utils.logger import get_logger
from src.ui.main_window import MainWindow
from src.ui.dialogs import LoginDialog
from src.db.database import init_db
from src.config import APP_NAME

log = get_logger()


def main():
    multiprocessing.freeze_support()
    ensure_dirs()
    log.info("Starting %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Set a default font that supports Sinhala glyphs
    font = QFont("Iskoola Pota", 10)
    app.setFont(font)

    # ── Comprehensive dark theme ─────────────────────────────
    app.setStyleSheet("""
        /* ── Base ─────────────────────────────────────── */
        QMainWindow, QDialog, QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
        QLabel {
            color: #e0e0e0;
        }

        /* ── Group boxes ──────────────────────────────── */
        QGroupBox {
            border: 1px solid #555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 14px;
            color: #ccc;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }

        /* ── Inputs ───────────────────────────────────── */
        QLineEdit, QTextEdit, QTextBrowser, QSpinBox,
        QComboBox, QDateEdit {
            background-color: #3c3f41;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 13px;
        }
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
        QComboBox:focus, QDateEdit:focus {
            border: 1px solid #4a8ab5;
        }

        /* ── ComboBox dropdown ────────────────────────── */
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #aaa;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3f41;
            color: #e0e0e0;
            selection-background-color: #3c6e91;
            selection-color: #fff;
            border: 1px solid #555;
            padding: 4px;
        }

        /* ── DateEdit ─────────────────────────────────── */
        QDateEdit::drop-down {
            border: none;
            width: 24px;
        }
        QDateEdit::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #aaa;
            margin-right: 6px;
        }
        QCalendarWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }

        /* ── List widgets ─────────────────────────────── */
        QListWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 4px;
            font-size: 13px;
        }
        QListWidget::item {
            padding: 6px 8px;
            border-bottom: 1px solid #3a3a3a;
        }
        QListWidget::item:alternate {
            background-color: #313131;
        }
        QListWidget::item:selected {
            background-color: #3c6e91;
            color: #fff;
        }
        QListWidget::item:hover {
            background-color: #383838;
        }

        /* ── Buttons ──────────────────────────────────── */
        QPushButton {
            background-color: #3c6e91;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 6px 14px;
            font-size: 13px;
        }
        QPushButton:hover  { background-color: #4a8ab5; }
        QPushButton:pressed { background-color: #2f5a78; }
        QPushButton:disabled {
            background-color: #444;
            color: #888;
        }

        /* ── Scrollbars ───────────────────────────────── */
        QScrollBar:vertical {
            width: 10px;
            background: #2b2b2b;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: #555;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6a6a6a;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            height: 10px;
            background: #2b2b2b;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background: #555;
            border-radius: 4px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #6a6a6a;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }

        /* ── Progress bar ─────────────────────────────── */
        QProgressBar {
            text-align: center;
            border: 1px solid #555;
            border-radius: 4px;
            background: #2b2b2b;
            color: #e0e0e0;
        }
        QProgressBar::chunk {
            background-color: #3c6e91;
            border-radius: 3px;
        }

        /* ── Menu bar ─────────────────────────────────── */
        QMenuBar {
            background: #333;
            color: #ddd;
            border-bottom: 1px solid #444;
        }
        QMenuBar::item:selected { background: #3c6e91; }
        QMenu {
            background: #3c3f41;
            color: #ddd;
            border: 1px solid #555;
        }
        QMenu::item:selected { background: #3c6e91; }
        QMenu::separator {
            height: 1px;
            background: #555;
            margin: 4px 8px;
        }

        /* ── Toolbar ──────────────────────────────────── */
        QToolBar {
            background: #333;
            border: none;
            border-bottom: 1px solid #444;
            spacing: 6px;
            padding: 4px 8px;
        }

        /* ── Status bar ───────────────────────────────── */
        QStatusBar {
            background: #333;
            color: #aaa;
            border-top: 1px solid #444;
        }

        /* ── Dock widgets ─────────────────────────────── */
        QDockWidget {
            color: #e0e0e0;
            titlebar-close-icon: url(none);
        }
        QDockWidget::title {
            background: #333;
            padding: 6px 8px;
            border: 1px solid #444;
            font-weight: bold;
        }
        QDockWidget::close-button, QDockWidget::float-button {
            background: transparent;
            border: none;
            padding: 2px;
        }
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background: #555;
            border-radius: 3px;
        }

        /* ── Scroll area ──────────────────────────────── */
        QScrollArea {
            background-color: #1e1e1e;
            border: none;
        }

        /* ── Tab widget (if used) ─────────────────────── */
        QTabWidget::pane {
            border: 1px solid #555;
            background: #2b2b2b;
        }
        QTabBar::tab {
            background: #333;
            color: #ccc;
            padding: 6px 14px;
            border: 1px solid #555;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #2b2b2b;
            color: #fff;
        }
        QTabBar::tab:hover {
            background: #3c3f41;
        }

        /* ── Input dialog / Message box ───────────────── */
        QInputDialog, QMessageBox {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
    """)

    # Initialize database (needed for login)
    init_db()

    # Show login dialog before main window
    login = LoginDialog()
    if login.exec_() != login.Accepted:
        sys.exit(0)
    login.deleteLater()          # explicitly destroy login window
    app.processEvents()          # flush pending deletions

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
