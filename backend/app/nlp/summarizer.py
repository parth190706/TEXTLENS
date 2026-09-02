"""
TextLens — Extractive summarizer using centroid-based TextRank approach.
Selects sentences most semantically similar to the document centroid.
Faithful to source: never invents text.
"""
from __future__ import annotations

from typing import List

import numpy as np
from loguru import logger


def generate_summary(
    sentences,
    embeddings: np.ndarray,
    top_n: int = 5,
    max_length_chars: int = 1200,
) -> str:
    """
    Selects top_n sentences most similar to the document centroid embedding.
    Returns them joined in document order.

    sentences: list of ProcessedSentence
    embeddings: normalized embedding matrix (N × dim)
    """
    if not sentences or embeddings.size == 0:
        return "No content available for summary generation."

    n = min(len(sentences), embeddings.shape[0])
    embeddings = embeddings[:n]

    # Document centroid
    centroid = embeddings.mean(axis=0)
    centroid_norm = np.linalg.norm(centroid)
    if centroid_norm > 0:
        centroid /= centroid_norm

    # Similarity to centroid
    sims = embeddings @ centroid

    # Select top_n but keep order
    top_indices = np.argsort(sims)[::-1][:top_n]
    top_indices_sorted = sorted(top_indices.tolist())

    selected: List[str] = []
    total_len = 0
    for idx in top_indices_sorted:
        text = sentences[idx].text
        if total_len + len(text) > max_length_chars:
            break
        selected.append(text)
        total_len += len(text)

    if not selected:
        selected = [sentences[0].text]

    summary = " ".join(selected)
    logger.info(f"Summary generated: {len(selected)} sentences, {len(summary)} chars")
    return summary


def generate_interpretation(
    summary: str,
    topics: List,       # list of ExtractedTopic
    relationships: List,  # list of DetectedRelationship
    sentences,
) -> str:
    """
    Generates an overall interpretation by combining the summary
    with high-level relationship and topic observations.
    This uses structured analysis — not a language model.
    """
    parts = [summary]

    if topics:
        topic_labels = [t.label for t in topics[:3]]
        parts.append(
            f"The document primarily covers: {'; '.join(topic_labels)}."
        )

    cause_effect = [r for r in relationships if r.relation_type == "cause_effect"]
    if cause_effect:
        r = cause_effect[0]
        src = sentences[r.source_index].text if r.source_index < len(sentences) else ""
        tgt = sentences[r.target_index].text if r.target_index < len(sentences) else ""
        if src and tgt:
            parts.append(
                f"A key causal relationship was identified: \"{src[:100]}...\" leads to \"{tgt[:100]}...\"."
            )

    contradictions = [r for r in relationships if r.relation_type == "contradiction"]
    if contradictions:
        parts.append(
            f"{len(contradictions)} possible contradiction(s) were detected, "
            "which may indicate conflicting information in the document."
        )

    return " ".join(parts)
