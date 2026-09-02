"""
TextLens — Relationship detection between sentences.
Uses cue words + semantic similarity.

Relation types:
  - cause_effect      (therefore, thus, consequently, as a result)
  - problem_solution  (however, to address, introduced, resolved)
  - support           (shows that, confirms, evidence)
  - similar           (high cosine similarity, ≥0.80)
  - contradiction     (near-similar topic, opposing polarity)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from loguru import logger

# ─── Cue word patterns ───────────────────────────────────────────

CAUSE_EFFECT_CUES = re.compile(
    r"\b(therefore|thus|consequently|as a result|hence|because|since|"
    r"led to|caused|resulting in|due to|owing to|this led|this caused)\b",
    re.IGNORECASE,
)

PROBLEM_SOLUTION_CUES = re.compile(
    r"\b(however|to address|to resolve|introduced|implemented|deployed|"
    r"challenge|difficulty|problem|issue|solution|resolved|tackled|"
    r"in response|to improve|to overcome)\b",
    re.IGNORECASE,
)

SUPPORT_CUES = re.compile(
    r"\b(shows that|confirms|evidence|supports|demonstrates|proves|"
    r"according to|data shows|figures show|this indicates|suggests that)\b",
    re.IGNORECASE,
)

NEGATION_WORDS = re.compile(
    r"\b(not|no|never|neither|nor|cannot|can't|won't|didn't|doesn't|"
    r"isn't|wasn't|weren't|don't|haven't|hadn't|wouldn't|couldn't|shouldn't)\b",
    re.IGNORECASE,
)

INCREASE_WORDS = re.compile(
    r"\b(increase|increased|grew|growth|rise|rose|improve|improved|gain|gained|"
    r"higher|more|greater|expanded|up|boost|boosted)\b",
    re.IGNORECASE,
)

DECREASE_WORDS = re.compile(
    r"\b(decrease|decreased|fell|decline|reduced|reduction|drop|dropped|"
    r"lower|less|fewer|shrunk|cut|down|loss|lost)\b",
    re.IGNORECASE,
)


# ─── Data structures ─────────────────────────────────────────────

@dataclass
class DetectedRelationship:
    source_index: int
    target_index: int
    relation_type: str
    confidence: float
    explanation: str
    cue_phrase: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────

def _polarity(text: str) -> str:
    """Simple polarity: positive / negative / neutral."""
    neg = bool(NEGATION_WORDS.search(text))
    inc = bool(INCREASE_WORDS.search(text))
    dec = bool(DECREASE_WORDS.search(text))

    if inc and not neg:
        return "positive"
    if dec and not neg:
        return "negative"
    if inc and neg:
        return "negative"
    if dec and neg:
        return "positive"
    return "neutral"


def _find_cue(text: str, pattern: re.Pattern) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0) if m else None


# ─── Main detector ───────────────────────────────────────────────

def detect_relationships(
    sentences,
    sim_matrix: np.ndarray,
    top_k_sentences: List[int],  # indices of important sentences to examine
    similarity_threshold: float = 0.80,
    contradiction_threshold: float = 0.65,
    window: int = 5,
) -> List[DetectedRelationship]:
    """
    sentences: list of ProcessedSentence (full doc)
    sim_matrix: N×N cosine similarity matrix
    top_k_sentences: indices of key sentences to compare
    """
    results: List[DetectedRelationship] = []
    seen: set = set()
    n = len(sentences)

    def add(rel: DetectedRelationship):
        key = (min(rel.source_index, rel.target_index),
               max(rel.source_index, rel.target_index),
               rel.relation_type)
        if key not in seen:
            seen.add(key)
            results.append(rel)

    for i in top_k_sentences:
        if i >= n:
            continue
        sent_i = sentences[i]
        text_i = sent_i.text

        # ── Cue-based: scan window around sentence ────────────────
        for j in range(max(0, i - window), min(n, i + window + 1)):
            if j == i:
                continue
            sent_j = sentences[j]
            text_j = sent_j.text

            # Cause-effect: look for cue in later sentence
            if j > i:
                cue = _find_cue(text_j, CAUSE_EFFECT_CUES)
                if cue:
                    add(DetectedRelationship(
                        source_index=i,
                        target_index=j,
                        relation_type="cause_effect",
                        confidence=0.80,
                        explanation=f"Causal cue '{cue}' found in target sentence.",
                        cue_phrase=cue,
                    ))

                cue = _find_cue(text_j, PROBLEM_SOLUTION_CUES)
                if cue:
                    add(DetectedRelationship(
                        source_index=i,
                        target_index=j,
                        relation_type="problem_solution",
                        confidence=0.72,
                        explanation=f"Problem-solution cue '{cue}' found.",
                        cue_phrase=cue,
                    ))

            # Support cues
            cue = _find_cue(text_j, SUPPORT_CUES)
            if cue:
                add(DetectedRelationship(
                    source_index=i,
                    target_index=j,
                    relation_type="support",
                    confidence=0.70,
                    explanation=f"Support cue '{cue}' found.",
                    cue_phrase=cue,
                ))

        # ── Similarity-based: compare key sentences ───────────────
        for j in top_k_sentences:
            if j <= i:
                continue
            if i >= sim_matrix.shape[0] or j >= sim_matrix.shape[0]:
                continue

            sim = float(sim_matrix[i, j])

            if sim >= similarity_threshold:
                add(DetectedRelationship(
                    source_index=i,
                    target_index=j,
                    relation_type="similar",
                    confidence=round(sim, 2),
                    explanation=f"Semantic similarity: {sim:.2f}",
                ))

            elif contradiction_threshold <= sim < similarity_threshold:
                pol_i = _polarity(sentences[i].text)
                pol_j = _polarity(sentences[j].text)
                if pol_i != pol_j and pol_i != "neutral" and pol_j != "neutral":
                    add(DetectedRelationship(
                        source_index=i,
                        target_index=j,
                        relation_type="contradiction",
                        confidence=round(sim * 0.85, 2),
                        explanation=(
                            f"Similar topic (similarity {sim:.2f}) but opposing polarity "
                            f"({pol_i} vs {pol_j})."
                        ),
                    ))

    logger.info(f"Detected {len(results)} relationships")
    return results
