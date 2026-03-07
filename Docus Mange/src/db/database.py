# ──────────────────────────────────────────────────────────────
# Database  –  Session & CRUD helpers
# ──────────────────────────────────────────────────────────────
import os
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import DB_PATH, DATA_DIR
from src.db.models import Base, PDFDocument, PageText, Category, AdminUser, _hash_password
from src.utils.logger import get_logger

log = get_logger(__name__)

# ── Engine / Session factory ────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
_engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
_SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(_engine)
    log.info("Database initialised at %s", DB_PATH)
    _seed_default_categories()
    _seed_default_admin()


def _seed_default_categories():
    """Insert default categories if the table is empty."""
    defaults = [
        "General", "Administrative", "Financial", "Legal",
        "Technical", "HR / Personnel", "Policy", "Other",
    ]
    with get_session() as s:
        if s.query(Category).count() == 0:
            for name in defaults:
                s.add(Category(name=name))
            log.info("Seeded %d default categories", len(defaults))


@contextmanager
def get_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Document helpers ────────────────────────────────────────

def add_document(file_path: str, file_name: str, total_pages: int,
                 circular_no: str = "", doc_type: str = "Circular",
                 doc_name: str = "",
                 doc_date: str = "", category: str = "") -> PDFDocument:
    with get_session() as s:
        doc = PDFDocument(
            file_path=file_path,
            file_name=file_name,
            total_pages=total_pages,
            circular_no=circular_no,
            doc_type=doc_type,
            doc_name=doc_name,
            doc_date=doc_date,
            category=category,
        )
        s.add(doc)
        s.flush()
        s.refresh(doc)
        doc_id = doc.id
    # return a detached-safe copy
    return get_document_by_id(doc_id)


def get_document_by_path(path: str) -> Optional[PDFDocument]:
    with get_session() as s:
        doc = s.query(PDFDocument).filter_by(file_path=path).first()
        if doc:
            s.expunge(doc)
        return doc


def get_document_by_id(doc_id: int) -> Optional[PDFDocument]:
    with get_session() as s:
        doc = s.query(PDFDocument).get(doc_id)
        if doc:
            s.expunge(doc)
        return doc


def get_all_documents() -> List[PDFDocument]:
    with get_session() as s:
        docs = s.query(PDFDocument).order_by(PDFDocument.added_at.desc()).all()
        for doc in docs:
            s.expunge(doc)
        return docs


def delete_document(doc_id: int):
    with get_session() as s:
        doc = s.query(PDFDocument).get(doc_id)
        if doc:
            s.delete(doc)
            log.info("Deleted document id=%s", doc_id)


def mark_indexed(doc_id: int):
    with get_session() as s:
        doc = s.query(PDFDocument).get(doc_id)
        if doc:
            doc.is_indexed = True


# ── Page-text helpers ───────────────────────────────────────

def save_page_texts(doc_id: int, pages: List[dict]):
    """
    Persist extracted texts.
    *pages* – list of dicts: {"page_number": int, "text": str, "ocr_used": bool}
    """
    with get_session() as s:
        for p in pages:
            pt = PageText(
                document_id=doc_id,
                page_number=p["page_number"],
                text=p["text"],
                ocr_used=p.get("ocr_used", False),
            )
            s.add(pt)
    log.info("Saved %d page texts for doc %d", len(pages), doc_id)


def get_page_texts(doc_id: int) -> List[PageText]:
    with get_session() as s:
        pages = (
            s.query(PageText)
            .filter_by(document_id=doc_id)
            .order_by(PageText.page_number)
            .all()
        )
        for p in pages:
            s.expunge(p)
        return pages


# ── Category helpers ────────────────────────────────────────

def get_all_categories() -> List[str]:
    """Return all category names sorted alphabetically."""
    with get_session() as s:
        cats = s.query(Category).order_by(Category.name).all()
        return [c.name for c in cats]


def add_category(name: str) -> bool:
    """Add a new category. Returns True if added, False if it already exists."""
    name = name.strip()
    if not name:
        return False
    with get_session() as s:
        if s.query(Category).filter_by(name=name).first():
            return False
        s.add(Category(name=name))
    log.info("Added category: %s", name)
    return True


def update_category(old_name: str, new_name: str) -> bool:
    """Rename a category. Returns True on success."""
    new_name = new_name.strip()
    if not new_name:
        return False
    with get_session() as s:
        cat = s.query(Category).filter_by(name=old_name).first()
        if not cat:
            return False
        if s.query(Category).filter_by(name=new_name).first():
            return False  # target name already exists
        cat.name = new_name
    log.info("Renamed category '%s' -> '%s'", old_name, new_name)
    return True


def delete_category(name: str) -> bool:
    """Delete a category by name. Returns True if deleted."""
    with get_session() as s:
        cat = s.query(Category).filter_by(name=name).first()
        if not cat:
            return False
        s.delete(cat)
    log.info("Deleted category: %s", name)
    return True


# ── Admin user helpers ──────────────────────────────────

def _seed_default_admin():
    """Create a default admin account if none exists."""
    with get_session() as s:
        if s.query(AdminUser).count() == 0:
            admin = AdminUser(username="admin")
            admin.set_password("admin123")
            s.add(admin)
            log.info("Seeded default admin account (admin / admin123)")


def authenticate_admin(username: str, password: str) -> bool:
    """Verify admin credentials. Returns True if valid."""
    with get_session() as s:
        user = s.query(AdminUser).filter_by(username=username).first()
        if user and user.check_password(password):
            return True
    return False
