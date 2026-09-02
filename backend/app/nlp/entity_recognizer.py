"""
TextLens — Named Entity Recognition using spaCy.
Extracts PERSON, ORG, GPE (location), DATE, CARDINAL, MONEY, PERCENT.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from app.core.config import settings

# ─── Lazy model loading ───────────────────────────────────────────

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            logger.info(f"Loading spaCy model: {settings.SPACY_MODEL}")
            _nlp = spacy.load(settings.SPACY_MODEL)
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.error(
                f"spaCy model '{settings.SPACY_MODEL}' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            raise
    return _nlp


# ─── Data Structures ─────────────────────────────────────────────

LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "GPE": "LOC",       # Geo-political entity → location
    "LOC": "LOC",
    "FAC": "LOC",
    "DATE": "DATE",
    "TIME": "DATE",
    "CARDINAL": "NUMBER",
    "ORDINAL": "NUMBER",
    "MONEY": "NUMBER",
    "PERCENT": "NUMBER",
    "QUANTITY": "NUMBER",
}


@dataclass
class ExtractedEntity:
    text: str
    label: str           # normalized label
    raw_label: str       # spaCy original
    sentence_index: int
    page_number: int
    count: int = 1


@dataclass
class EntityResult:
    entities: List[ExtractedEntity] = field(default_factory=list)

    @property
    def by_label(self) -> Dict[str, List[ExtractedEntity]]:
        groups: Dict[str, List[ExtractedEntity]] = defaultdict(list)
        for e in self.entities:
            groups[e.label].append(e)
        return dict(groups)


# ─── Extraction ───────────────────────────────────────────────────

def extract_entities(sentences) -> EntityResult:
    """
    sentences: list of ProcessedSentence
    Returns EntityResult with deduplicated, counted entities.
    """
    nlp = get_nlp()
    entity_counts: Dict[tuple, dict] = {}  # (text_lower, label) → info

    for sent in sentences:
        doc = nlp(sent.text)
        for ent in doc.ents:
            label = LABEL_MAP.get(ent.label_, "OTHER")
            key = (ent.text.strip().lower(), label)
            if key in entity_counts:
                entity_counts[key]["count"] += 1
            else:
                entity_counts[key] = {
                    "text": ent.text.strip(),
                    "label": label,
                    "raw_label": ent.label_,
                    "sentence_index": sent.sentence_index,
                    "page_number": sent.page_number,
                    "count": 1,
                }

    entities = [
        ExtractedEntity(**v)
        for v in entity_counts.values()
        if len(v["text"]) > 1  # skip single-char matches
    ]

    # Sort by count desc
    entities.sort(key=lambda e: e.count, reverse=True)
    logger.info(f"Extracted {len(entities)} unique entities")
    return EntityResult(entities=entities)
