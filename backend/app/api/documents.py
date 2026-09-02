"""
TextLens — Document API routes.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db import get_db, Document, Analysis, Finding, Relationship, EvidenceLink, Entity, Topic, Sentence
from app.schemas import (
    DocumentUploadResponse, DocumentListItem, DocumentDetail,
    AnalysisStatusResponse, AnalysisResponse, FindingSchema,
    RelationshipSchema, EvidenceSchema, EntitiesResponse, EntitySchema,
    TopicSchema, TopicKeyword,
)
from app.services.document_service import save_upload, get_document, list_documents
from app.services.analysis_service import run_analysis

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ── Upload ──────────────────────────────────────────────────────

@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, DOCX, or TXT document."""
    doc = await save_upload(file, db)
    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        created_at=doc.created_at,
    )


# ── List ─────────────────────────────────────────────────────────

@router.get("", response_model=List[DocumentListItem])
async def get_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    docs = await list_documents(db)
    return [
        DocumentListItem(
            id=d.id,
            original_filename=d.original_filename,
            file_type=d.file_type,
            file_size=d.file_size,
            status=d.status,
            page_count=d.page_count,
            sentence_count=d.sentence_count,
            created_at=d.created_at,
        )
        for d in docs
    ]


# ── Get one ───────────────────────────────────────────────────────

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await get_document(doc_id, db)
    return DocumentDetail(
        id=doc.id,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        page_count=doc.page_count,
        sentence_count=doc.sentence_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ── Trigger analysis ──────────────────────────────────────────────

@router.post("/{doc_id}/analyze", status_code=202)
async def analyze_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger analysis pipeline for a document (async background job)."""
    doc = await get_document(doc_id, db)
    if doc.status == "processing":
        raise HTTPException(status_code=409, detail="Analysis already in progress.")

    background_tasks.add_task(run_analysis, doc_id, db)
    logger.info(f"Analysis queued for document {doc_id}")
    return {"message": "Analysis started.", "document_id": doc_id}


# ── Status polling ────────────────────────────────────────────────

@router.get("/{doc_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await get_document(doc_id, db)
    return AnalysisStatusResponse(
        document_id=doc.id,
        status=doc.status,
        error_message=doc.error_message,
        page_count=doc.page_count,
        sentence_count=doc.sentence_count,
    )


# ── Full analysis result ──────────────────────────────────────────

@router.get("/{doc_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await get_document(doc_id, db)
    if doc.status != "completed":
        raise HTTPException(
            status_code=422,
            detail=f"Analysis not complete. Current status: {doc.status}",
        )

    # Analysis record
    an_res = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
    analysis = an_res.scalar_one_or_none()

    # Findings
    findings = await _get_findings(doc_id, db)

    # Entities
    entities_resp = await _get_entities_response(doc_id, db)

    # Topics
    topics = await _get_topics(doc_id, db)

    # Relationships (non-contradiction)
    rels, contradictions = await _get_relationships(doc_id, db)

    # Evidence
    evidence = await _get_evidence(doc_id, db)

    return AnalysisResponse(
        document_id=doc_id,
        summary=analysis.summary if analysis else None,
        overall_interpretation=analysis.overall_interpretation if analysis else None,
        processing_duration_seconds=analysis.processing_duration_seconds if analysis else None,
        key_findings=findings,
        entities=entities_resp,
        topics=topics,
        relationships=rels,
        evidence=evidence,
        contradictions=contradictions,
        created_at=analysis.created_at if analysis else None,
    )


# ── Sub-routes ────────────────────────────────────────────────────

@router.get("/{doc_id}/findings", response_model=List[FindingSchema])
async def get_findings(doc_id: str, db: AsyncSession = Depends(get_db)):
    await get_document(doc_id, db)
    return await _get_findings(doc_id, db)


@router.get("/{doc_id}/entities")
async def get_entities(doc_id: str, db: AsyncSession = Depends(get_db)):
    await get_document(doc_id, db)
    return await _get_entities_response(doc_id, db)


@router.get("/{doc_id}/topics", response_model=List[TopicSchema])
async def get_topics(doc_id: str, db: AsyncSession = Depends(get_db)):
    await get_document(doc_id, db)
    return await _get_topics(doc_id, db)


@router.get("/{doc_id}/relationships", response_model=List[RelationshipSchema])
async def get_relationships(doc_id: str, db: AsyncSession = Depends(get_db)):
    await get_document(doc_id, db)
    rels, contradictions = await _get_relationships(doc_id, db)
    return rels + contradictions


@router.get("/{doc_id}/evidence", response_model=List[EvidenceSchema])
async def get_evidence(doc_id: str, db: AsyncSession = Depends(get_db)):
    await get_document(doc_id, db)
    return await _get_evidence(doc_id, db)


# ── Internal helpers ──────────────────────────────────────────────

async def _get_findings(doc_id: str, db: AsyncSession) -> List[FindingSchema]:
    res = await db.execute(
        select(Finding).where(Finding.document_id == doc_id).order_by(Finding.rank)
    )
    return [
        FindingSchema(
            id=f.id, rank=f.rank, text=f.text,
            importance_score=f.importance_score,
            page_number=f.page_number, reason=f.reason,
        )
        for f in res.scalars().all()
    ]


async def _get_entities_response(doc_id: str, db: AsyncSession) -> EntitiesResponse:
    res = await db.execute(
        select(Entity).where(Entity.document_id == doc_id).order_by(Entity.count.desc())
    )
    all_entities = res.scalars().all()

    def _es(e: Entity) -> EntitySchema:
        return EntitySchema(
            id=e.id, text=e.text, label=e.label,
            normalized=e.normalized, page_number=e.page_number, count=e.count,
        )

    label_map = {
        "PERSON": "people", "ORG": "organizations", "LOC": "locations",
        "DATE": "dates", "NUMBER": "numbers",
    }
    grouped: dict = {k: [] for k in label_map.values()}
    grouped["other"] = []

    for e in all_entities:
        key = label_map.get(e.label, "other")
        grouped[key].append(_es(e))

    return EntitiesResponse(document_id=doc_id, **grouped)


async def _get_topics(doc_id: str, db: AsyncSession) -> List[TopicSchema]:
    res = await db.execute(
        select(Topic).where(Topic.document_id == doc_id)
        .order_by(Topic.relevance_score.desc())
    )
    return [
        TopicSchema(
            id=t.id,
            label=t.label,
            keywords=[TopicKeyword(**kw) for kw in (t.keywords or [])],
            relevance_score=t.relevance_score,
        )
        for t in res.scalars().all()
    ]


async def _get_relationships(doc_id: str, db: AsyncSession):
    # Load relationships then load sentences separately
    rel_res = await db.execute(
        select(Relationship).where(Relationship.document_id == doc_id)
    )
    rels = rel_res.scalars().all()

    # Load all relevant sentences in one query
    sent_ids = set()
    for r in rels:
        sent_ids.add(r.source_sentence_id)
        sent_ids.add(r.target_sentence_id)

    if sent_ids:
        sent_res = await db.execute(
            select(Sentence).where(Sentence.id.in_(sent_ids))
        )
        sent_map = {s.id: s for s in sent_res.scalars().all()}
    else:
        sent_map = {}

    normal: List[RelationshipSchema] = []
    contradictions: List[RelationshipSchema] = []

    for r in rels:
        src = sent_map.get(r.source_sentence_id)
        tgt = sent_map.get(r.target_sentence_id)
        schema = RelationshipSchema(
            id=r.id,
            source_text=src.text if src else "",
            target_text=tgt.text if tgt else "",
            source_page=src.page_number if src else None,
            target_page=tgt.page_number if tgt else None,
            relation_type=r.relation_type,
            confidence=r.confidence,
            explanation=r.explanation,
            cue_phrase=r.cue_phrase,
        )
        if r.relation_type == "contradiction":
            contradictions.append(schema)
        else:
            normal.append(schema)

    return normal, contradictions


async def _get_evidence(doc_id: str, db: AsyncSession) -> List[EvidenceSchema]:
    ev_res = await db.execute(
        select(EvidenceLink).where(EvidenceLink.document_id == doc_id)
        .order_by(EvidenceLink.similarity_score.desc())
    )
    ev_list = ev_res.scalars().all()

    if not ev_list:
        return []

    # Load findings and sentences
    f_ids = {e.finding_id for e in ev_list}
    s_ids = {e.sentence_id for e in ev_list}

    f_res = await db.execute(select(Finding).where(Finding.id.in_(f_ids)))
    f_map = {f.id: f for f in f_res.scalars().all()}

    s_res = await db.execute(select(Sentence).where(Sentence.id.in_(s_ids)))
    s_map = {s.id: s for s in s_res.scalars().all()}

    return [
        EvidenceSchema(
            id=e.id,
            finding_text=f_map[e.finding_id].text if e.finding_id in f_map else "",
            evidence_text=s_map[e.sentence_id].text if e.sentence_id in s_map else "",
            page_number=e.page_number,
            similarity_score=e.similarity_score,
        )
        for e in ev_list
        if e.finding_id in f_map
    ]
