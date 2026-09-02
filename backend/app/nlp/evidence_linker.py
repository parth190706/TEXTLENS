"""
TextLens — Evidence linking.
For each key finding, finds the most similar supporting sentence in the document.
Uses pre-computed embeddings to avoid redundant inference.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from loguru import logger


@dataclass
class EvidenceLinkResult:
    finding_sentence_index: int
    finding_text: str
    evidence_sentence_index: int
    evidence_text: str
    page_number: Optional[int]
    similarity_score: float


def find_evidence(
    finding_indices: List[int],
    all_sentences,
    embeddings: np.ndarray,
    min_similarity: float = 0.50,
) -> List[EvidenceLinkResult]:
    """
    finding_indices: sentence indices selected as key findings
    all_sentences: list of ProcessedSentence
    embeddings: full embedding matrix (N × dim)
    Returns one EvidenceLink per finding (best matching non-identical sentence).
    """
    if embeddings.size == 0:
        return []

    results: List[EvidenceLinkResult] = []

    for fi in finding_indices:
        if fi >= embeddings.shape[0]:
            continue

        query_vec = embeddings[fi]  # already normalized
        sims = embeddings @ query_vec  # cosine similarities

        # Exclude the finding itself
        sims[fi] = -1.0

        best_j = int(np.argmax(sims))
        best_sim = float(sims[best_j])

        if best_sim < min_similarity:
            continue

        results.append(
            EvidenceLinkResult(
                finding_sentence_index=fi,
                finding_text=all_sentences[fi].text,
                evidence_sentence_index=best_j,
                evidence_text=all_sentences[best_j].text,
                page_number=all_sentences[best_j].page_number,
                similarity_score=round(best_sim, 3),
            )
        )

    logger.info(f"Found {len(results)} evidence links for {len(finding_indices)} findings")
    return results
