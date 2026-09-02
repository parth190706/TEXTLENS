"""
TextLens — Sentence embeddings using Sentence-Transformers (all-MiniLM-L6-v2).
Lazy-loaded singleton. CPU-compatible.
"""
from __future__ import annotations

from typing import List

import numpy as np
from loguru import logger

from app.core.config import settings

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as exc:
            logger.error(f"Failed to load embedding model: {exc}")
            raise
    return _model


def embed_sentences(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Returns a numpy array of shape (N, embedding_dim).
    Handles empty input gracefully.
    """
    if not texts:
        return np.array([])

    # Truncate if too many sentences
    max_n = settings.MAX_SENTENCES_FOR_EMBEDDING
    if len(texts) > max_n:
        logger.warning(f"Truncating embedding input from {len(texts)} to {max_n} sentences")
        texts = texts[:max_n]

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,   # cosine similarity via dot product
    )
    return embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors (normalized embeddings → dot product)."""
    if a.ndim == 1 and b.ndim == 1:
        return float(np.dot(a, b))
    raise ValueError("Expected 1-D arrays")


def similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarity matrix (N x N) for normalized embeddings."""
    return embeddings @ embeddings.T
