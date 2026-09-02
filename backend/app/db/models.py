"""
TextLens — SQLAlchemy database models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)
    upload_path = Column(String(500), nullable=False)
    status = Column(
        SAEnum(
            "uploaded", "processing", "completed", "failed",
            name="document_status"
        ),
        default="uploaded",
        nullable=False,
    )
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    sentences = relationship("Sentence", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="document", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document", cascade="all, delete-orphan")
    relationships_list = relationship("Relationship", back_populates="document", cascade="all, delete-orphan")
    evidence_links = relationship("EvidenceLink", back_populates="document", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="pages")
    sentences = relationship("Sentence", back_populates="page")


class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True)
    sentence_index = Column(Integer, nullable=False)  # global index in document
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.0)

    document = relationship("Document", back_populates="sentences")
    page = relationship("DocumentPage", back_populates="sentences")
    entities = relationship("Entity", back_populates="sentence")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=True)
    text = Column(String(500), nullable=False)
    label = Column(String(50), nullable=False)  # PERSON, ORG, GPE, DATE, CARDINAL, etc.
    normalized = Column(String(500), nullable=True)
    page_number = Column(Integer, nullable=True)
    count = Column(Integer, default=1)

    document = relationship("Document", back_populates="entities")
    sentence = relationship("Sentence", back_populates="entities")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    topic_index = Column(Integer, nullable=False)
    label = Column(String(255), nullable=False)
    keywords = Column(JSON, nullable=False)  # list of {word, weight}
    relevance_score = Column(Float, default=0.0)

    document = relationship("Document", back_populates="topics")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.0)
    page_number = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)  # why it was selected

    document = relationship("Document", back_populates="findings")
    sentence = relationship("Sentence")
    evidence = relationship("EvidenceLink", back_populates="finding", cascade="all, delete-orphan")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    source_sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=False)
    target_sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=False)
    relation_type = Column(
        SAEnum(
            "cause_effect", "problem_solution", "support",
            "similar", "contradiction",
            name="relation_type"
        ),
        nullable=False,
    )
    confidence = Column(Float, default=0.5)
    explanation = Column(Text, nullable=True)
    cue_phrase = Column(String(255), nullable=True)

    document = relationship("Document", back_populates="relationships_list")
    source_sentence = relationship("Sentence", foreign_keys=[source_sentence_id])
    target_sentence = relationship("Sentence", foreign_keys=[target_sentence_id])


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=False)
    sentence_id = Column(String(36), ForeignKey("sentences.id"), nullable=False)
    similarity_score = Column(Float, default=0.0)
    page_number = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="evidence_links")
    finding = relationship("Finding", back_populates="evidence")
    sentence = relationship("Sentence")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    overall_interpretation = Column(Text, nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column(JSON, nullable=True)  # extra stats

    document = relationship("Document", back_populates="analysis")
