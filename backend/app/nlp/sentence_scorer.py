"""
TextLens — Sentence importance scoring using TF-IDF + entity density + position.
Returns scores between 0.0 and 1.0 for each sentence.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger


@dataclass
class ScoredSentence:
    sentence_index: int
    text: str
    importance_score: float
    reason: str


def _has_number(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _entity_density(text: str, entity_texts: List[str]) -> float:
    """Fraction of words in sentence that are part of a named entity."""
    words = text.lower().split()
    if not words:
        return 0.0
    hit = sum(1 for w in words if any(w in e.lower() for e in entity_texts))
    return hit / len(words)


def score_sentences(
    sentences,
    entity_texts: List[str],
    top_n: int = 10,
) -> List[ScoredSentence]:
    """
    sentences: list of ProcessedSentence
    entity_texts: list of entity string texts (for density scoring)
    Returns list of ScoredSentence sorted by importance_score desc.
    """
    if not sentences:
        return []

    texts = [s.text for s in sentences]

    # ── TF-IDF component ──────────────────────────────────────────
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        # Average TF-IDF score per sentence
        tfidf_scores = np.array(tfidf_matrix.mean(axis=1)).flatten()
        # Normalize to [0, 1]
        max_t = tfidf_scores.max() or 1.0
        tfidf_scores = tfidf_scores / max_t
    except Exception:
        tfidf_scores = np.zeros(len(texts))

    # ── Position component ────────────────────────────────────────
    n = len(sentences)
    position_scores = np.array(
        [1.0 if i < 3 or i >= n - 3 else 0.5 for i in range(n)],
        dtype=float,
    )

    # ── Entity density component ──────────────────────────────────
    entity_scores = np.array(
        [_entity_density(s.text, entity_texts) for s in sentences],
        dtype=float,
    )

    # ── Number presence bonus ─────────────────────────────────────
    number_scores = np.array(
        [0.3 if _has_number(s.text) else 0.0 for s in sentences],
        dtype=float,
    )

    # ── Combined weighted score ───────────────────────────────────
    combined = (
        0.50 * tfidf_scores
        + 0.20 * position_scores
        + 0.20 * entity_scores
        + 0.10 * number_scores
    )

    # Normalize again
    max_c = combined.max() or 1.0
    combined = combined / max_c

    results: List[ScoredSentence] = []
    for i, sent in enumerate(sentences):
        reasons = []
        if tfidf_scores[i] > 0.6:
            reasons.append("high term relevance")
        if entity_scores[i] > 0.3:
            reasons.append("contains named entities")
        if _has_number(sent.text):
            reasons.append("contains numeric information")
        if position_scores[i] > 0.5:
            reasons.append("appears at document boundary")

        results.append(
            ScoredSentence(
                sentence_index=sent.sentence_index,
                text=sent.text,
                importance_score=float(combined[i]),
                reason="; ".join(reasons) or "general relevance",
            )
        )

    results.sort(key=lambda s: s.importance_score, reverse=True)
    logger.info(f"Scored {len(results)} sentences; top score: {results[0].importance_score:.3f}")
    return results
