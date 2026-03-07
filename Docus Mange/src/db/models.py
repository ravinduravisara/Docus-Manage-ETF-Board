# ──────────────────────────────────────────────────────────────
# Database  –  SQLAlchemy models
# ──────────────────────────────────────────────────────────────
import datetime
import hashlib
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AdminUser(Base):
    """Application administrator account."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(256), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    def set_password(self, password: str):
        self.password_hash = _hash_password(password)

    def check_password(self, password: str) -> bool:
        return self.password_hash == _hash_password(password)

    def __repr__(self):
        return f"<AdminUser id={self.id} username='{self.username}'>"


class Category(Base):
    """User-defined document category."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False)

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"


class PDFDocument(Base):
    """Represents a single PDF file that has been imported."""
    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(1024), unique=True, nullable=False)
    file_name = Column(String(512), nullable=False)
    circular_no = Column(String(256), default="")
    doc_type = Column(String(256), default="Circular")
    doc_name = Column(String(512), default="")
    doc_date = Column(String(64), default="")
    category = Column(String(256), default="")
    total_pages = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    pages = relationship("PageText", back_populates="document",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PDFDocument id={self.id} name='{self.file_name}'>"


class PageText(Base):
    """Stores the extracted / OCR'd text for a single page."""
    __tablename__ = "page_texts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("pdf_documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)       # 0-based
    text = Column(Text, default="")
    ocr_used = Column(Boolean, default=False)

    document = relationship("PDFDocument", back_populates="pages")

    def __repr__(self):
        return (f"<PageText doc={self.document_id} "
                f"page={self.page_number}>")
