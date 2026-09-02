"""
TextLens — Document Service.
Handles file upload, validation, storage, and DB persistence.
"""
from __future__ import annotations

import hashlib
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Document

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _sanitize_filename(filename: str) -> str:
    """Keep only safe characters in filenames."""
    from pathlib import Path
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    safe_stem = "".join(c if c.isalnum() or c in "-_." else "_" for c in stem)
    return f"{safe_stem[:100]}{suffix}"


async def save_upload(
    upload: UploadFile,
    db: AsyncSession,
) -> Document:
    """
    Validate and save an uploaded file.
    Returns the created Document DB record.
    """
    # ── Filename validation ────────────────────────────────────────
    original = upload.filename or "unknown"
    suffix = Path(original).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: PDF, DOCX, TXT.",
        )

    # ── Read content ───────────────────────────────────────────────
    content = await upload.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size: {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # ── Magic byte / MIME validation ──────────────────────────────
    _validate_file_magic(content, suffix)

    # ── Save to disk ───────────────────────────────────────────────
    safe_name = _sanitize_filename(original)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest_path = settings.upload_path / unique_name
    dest_path.write_bytes(content)

    logger.info(f"Saved upload: {unique_name} ({file_size} bytes)")

    # ── Persist to DB ──────────────────────────────────────────────
    doc = Document(
        filename=unique_name,
        original_filename=original,
        file_type=suffix.lstrip("."),
        file_size=file_size,
        upload_path=str(dest_path),
        status="uploaded",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


def _validate_file_magic(content: bytes, suffix: str) -> None:
    """Check magic bytes to prevent MIME spoofing."""
    if suffix == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="File does not appear to be a valid PDF.",
            )
    elif suffix == ".docx":
        # DOCX is a ZIP file
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=400,
                detail="File does not appear to be a valid DOCX.",
            )
    # TXT has no magic bytes — accept as-is


async def get_document(doc_id: str, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())
