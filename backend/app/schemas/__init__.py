"""
TextLens — Pydantic schemas for API request/response.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ─────────────────────────── Document ────────────────────────────

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListItem(BaseModel):
    id: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    page_count: Optional[int] = None
    sentence_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(DocumentListItem):
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


# ─────────────────────────── Status ───────────────────────────────

class AnalysisStatusResponse(BaseModel):
    document_id: str
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    sentence_count: Optional[int] = None


# ─────────────────────────── Entity ───────────────────────────────

class EntitySchema(BaseModel):
    id: str
    text: str
    label: str
    normalized: Optional[str] = None
    page_number: Optional[int] = None
    count: int

    class Config:
        from_attributes = True


class EntitiesResponse(BaseModel):
    document_id: str
    people: List[EntitySchema] = []
    organizations: List[EntitySchema] = []
    locations: List[EntitySchema] = []
    dates: List[EntitySchema] = []
    numbers: List[EntitySchema] = []
    other: List[EntitySchema] = []


# ─────────────────────────── Topic ────────────────────────────────

class TopicKeyword(BaseModel):
    word: str
    weight: float


class TopicSchema(BaseModel):
    id: str
    label: str
    keywords: List[TopicKeyword]
    relevance_score: float

    class Config:
        from_attributes = True


# ─────────────────────────── Finding ──────────────────────────────

class FindingSchema(BaseModel):
    id: str
    rank: int
    text: str
    importance_score: float
    page_number: Optional[int] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────── Relationship ─────────────────────────

class RelationshipSchema(BaseModel):
    id: str
    source_text: str
    target_text: str
    source_page: Optional[int] = None
    target_page: Optional[int] = None
    relation_type: str
    confidence: float
    explanation: Optional[str] = None
    cue_phrase: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────── Evidence ─────────────────────────────

class EvidenceSchema(BaseModel):
    id: str
    finding_text: str
    evidence_text: str
    page_number: Optional[int] = None
    similarity_score: float

    class Config:
        from_attributes = True


# ─────────────────────────── Analysis ─────────────────────────────

class AnalysisResponse(BaseModel):
    document_id: str
    summary: Optional[str] = None
    overall_interpretation: Optional[str] = None
    processing_duration_seconds: Optional[float] = None
    key_findings: List[FindingSchema] = []
    entities: EntitiesResponse
    topics: List[TopicSchema] = []
    relationships: List[RelationshipSchema] = []
    evidence: List[EvidenceSchema] = []
    contradictions: List[RelationshipSchema] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────── Error ────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
