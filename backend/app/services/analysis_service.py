"""
TextLens — Analysis Pipeline Orchestrator.
Runs the full NLP pipeline and persists results to the database.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.db.models import (
    Document, DocumentPage, Sentence, Entity, Topic,
    Finding, Relationship, EvidenceLink, Analysis,
)
from app.nlp import (
    extract_document, process_pages, extract_entities,
    score_sentences, extract_topics, embed_sentences,
    similarity_matrix, detect_relationships, find_evidence,
    generate_summary, generate_interpretation,
    EvidenceLinkResult,
)


async def run_analysis(doc_id: str, db: AsyncSession) -> None:
    """
    Full pipeline for a document. Updates document status throughout.
    Called as a background task.
    """
    start = time.time()

    # ── Load document record ───────────────────────────────────────
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        logger.error(f"Document {doc_id} not found for analysis")
        return

    await _set_status(doc, "processing", db)

    try:
        # ── STAGE 1: Extract text ──────────────────────────────────
        logger.info(f"[{doc_id}] Stage 1: Extracting text from {doc.upload_path}")
        extraction = extract_document(Path(doc.upload_path))

        if not extraction.success:
            await _set_status(doc, "failed", db, extraction.error)
            return

        # ── STAGE 2: Clean + split sentences ──────────────────────
        logger.info(f"[{doc_id}] Stage 2: Processing text")
        processed = process_pages(extraction.pages)

        if not processed:
            await _set_status(doc, "failed", db, "No sentences could be extracted.")
            return

        # ── STAGE 3: Persist pages + sentences ────────────────────
        logger.info(f"[{doc_id}] Stage 3: Persisting pages/sentences")

        # Clear any existing data (re-analysis support)
        await _clear_existing(doc_id, db)

        page_id_map: dict = {}  # page_number → DB id
        for ep in extraction.pages:
            pg = DocumentPage(
                document_id=doc_id,
                page_number=ep.page_number,
                raw_text=ep.text,
                word_count=ep.word_count,
            )
            db.add(pg)
            await db.flush()
            page_id_map[ep.page_number] = pg.id

        sent_db_list: list[Sentence] = []
        for ps in processed:
            s = Sentence(
                document_id=doc_id,
                page_id=page_id_map.get(ps.page_number),
                sentence_index=ps.sentence_index,
                page_number=ps.page_number,
                section=ps.section,
                text=ps.text,
            )
            db.add(s)
            sent_db_list.append(s)

        await db.flush()

        # Map sentence_index → DB sentence (with id)
        idx_to_sent: dict = {s.sentence_index: s for s in sent_db_list}

        # ── STAGE 4: Named entity recognition ─────────────────────
        logger.info(f"[{doc_id}] Stage 4: Entity recognition")
        entity_result = extract_entities(processed)
        entity_texts = [e.text for e in entity_result.entities]

        for ent in entity_result.entities:
            sent_db = idx_to_sent.get(ent.sentence_index)
            e = Entity(
                document_id=doc_id,
                sentence_id=sent_db.id if sent_db else None,
                text=ent.text,
                label=ent.label,
                normalized=ent.text.lower(),
                page_number=ent.page_number,
                count=ent.count,
            )
            db.add(e)

        # ── STAGE 5: Importance scoring ────────────────────────────
        logger.info(f"[{doc_id}] Stage 5: Scoring sentences")
        scored = score_sentences(processed, entity_texts)

        # Update sentence importance in DB
        for sc in scored:
            s_db = idx_to_sent.get(sc.sentence_index)
            if s_db:
                s_db.importance_score = sc.importance_score

        # ── STAGE 6: Topic modeling ────────────────────────────────
        logger.info(f"[{doc_id}] Stage 6: Topic modeling")
        topics = extract_topics(processed)
        for t in topics:
            t_db = Topic(
                document_id=doc_id,
                topic_index=t.topic_index,
                label=t.label,
                keywords=[{"word": kw.word, "weight": kw.weight} for kw in t.keywords],
                relevance_score=t.relevance_score,
            )
            db.add(t_db)

        # ── STAGE 7: Embeddings + similarity ──────────────────────
        logger.info(f"[{doc_id}] Stage 7: Computing embeddings")
        texts = [ps.text for ps in processed]
        embeddings = embed_sentences(texts)

        sim_mat = similarity_matrix(embeddings) if embeddings.size > 0 else None

        # ── STAGE 8: Key findings ──────────────────────────────────
        logger.info(f"[{doc_id}] Stage 8: Selecting key findings")
        top_n_findings = min(10, len(scored))
        top_scored = scored[:top_n_findings]
        top_indices = [s.sentence_index for s in top_scored]

        finding_id_map: dict = {}  # sentence_index → Finding DB id
        for rank, sc in enumerate(top_scored, start=1):
            s_db = idx_to_sent.get(sc.sentence_index)
            if not s_db:
                continue
            f = Finding(
                document_id=doc_id,
                sentence_id=s_db.id,
                rank=rank,
                text=sc.text,
                importance_score=sc.importance_score,
                page_number=s_db.page_number,
                reason=sc.reason,
            )
            db.add(f)
            await db.flush()
            finding_id_map[sc.sentence_index] = f

        # ── STAGE 9: Relationships ─────────────────────────────────
        logger.info(f"[{doc_id}] Stage 9: Detecting relationships")
        relationships = []
        if sim_mat is not None:
            relationships = detect_relationships(processed, sim_mat, top_indices)
            for rel in relationships:
                src_db = idx_to_sent.get(rel.source_index)
                tgt_db = idx_to_sent.get(rel.target_index)
                if not src_db or not tgt_db:
                    continue
                r = Relationship(
                    document_id=doc_id,
                    source_sentence_id=src_db.id,
                    target_sentence_id=tgt_db.id,
                    relation_type=rel.relation_type,
                    confidence=rel.confidence,
                    explanation=rel.explanation,
                    cue_phrase=rel.cue_phrase,
                )
                db.add(r)

        # ── STAGE 10: Evidence linking ─────────────────────────────
        logger.info(f"[{doc_id}] Stage 10: Linking evidence")
        evidence_links = []
        if embeddings.size > 0:
            evidence_links = find_evidence(top_indices, processed, embeddings)
            for ev in evidence_links:
                f_db = finding_id_map.get(ev.finding_sentence_index)
                ev_sent_db = idx_to_sent.get(ev.evidence_sentence_index)
                if not f_db or not ev_sent_db:
                    continue
                el = EvidenceLink(
                    document_id=doc_id,
                    finding_id=f_db.id,
                    sentence_id=ev_sent_db.id,
                    similarity_score=ev.similarity_score,
                    page_number=ev.page_number,
                )
                db.add(el)

        # ── STAGE 11: Summary ──────────────────────────────────────
        logger.info(f"[{doc_id}] Stage 11: Generating summary")
        summary = "No summary available."
        interpretation = ""
        if embeddings.size > 0:
            summary = generate_summary(processed, embeddings)
            interpretation = generate_interpretation(
                summary, topics, relationships, processed
            )

        # ── STAGE 12: Persist Analysis record ─────────────────────
        duration = round(time.time() - start, 2)
        analysis = Analysis(
            document_id=doc_id,
            summary=summary,
            overall_interpretation=interpretation,
            processing_duration_seconds=duration,
            meta={
                "sentence_count": len(processed),
                "page_count": len(extraction.pages),
                "entity_count": len(entity_result.entities),
                "topic_count": len(topics),
                "relationship_count": len(relationships),
                "finding_count": len(top_scored),
            },
        )
        db.add(analysis)

        # Update document stats
        doc.status = "completed"
        doc.page_count = len(extraction.pages)
        doc.sentence_count = len(processed)
        await db.commit()

        logger.info(f"[{doc_id}] Analysis complete in {duration:.1f}s")

    except Exception as exc:
        logger.exception(f"[{doc_id}] Analysis pipeline failed: {exc}")
        await _set_status(doc, "failed", db, str(exc))


async def _set_status(doc: Document, status: str, db: AsyncSession, error: str = None):
    doc.status = status
    if error:
        doc.error_message = error[:1000]
    await db.commit()


async def _clear_existing(doc_id: str, db: AsyncSession):
    """Remove previous analysis data for re-analysis."""
    # Order matters due to FK constraints
    for model in [EvidenceLink, Relationship, Finding, Entity, Topic, Sentence, DocumentPage, Analysis]:
        stmt = delete(model).where(model.document_id == doc_id)
        await db.execute(stmt)
    await db.flush()
