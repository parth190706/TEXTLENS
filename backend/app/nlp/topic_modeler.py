"""
TextLens — Topic modeling using TF-IDF + LDA (scikit-learn).
No GPU required. Returns human-readable topic labels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from loguru import logger


@dataclass
class TopicWord:
    word: str
    weight: float


@dataclass
class ExtractedTopic:
    topic_index: int
    label: str          # top keywords joined
    keywords: List[TopicWord] = field(default_factory=list)
    relevance_score: float = 0.0


def extract_topics(sentences, n_topics: int = 5, n_top_words: int = 8) -> List[ExtractedTopic]:
    """
    sentences: list of ProcessedSentence
    Returns list of ExtractedTopic sorted by relevance_score desc.
    """
    texts = [s.text for s in sentences]
    if len(texts) < 3:
        logger.warning("Too few sentences for topic modeling")
        return []

    # Limit n_topics to number of texts
    n_topics = min(n_topics, len(texts) // 2, 8)
    if n_topics < 2:
        n_topics = 2

    try:
        vectorizer = CountVectorizer(
            max_features=2000,
            stop_words="english",
            min_df=1,
            max_df=0.95,
        )
        dtm = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20,
        )
        lda.fit(dtm)

        # Document-topic distribution to score relevance
        doc_topic = lda.transform(dtm)
        topic_relevance = doc_topic.mean(axis=0)

        topics: List[ExtractedTopic] = []
        for idx, topic_vec in enumerate(lda.components_):
            top_indices = topic_vec.argsort()[:-n_top_words - 1:-1]
            keywords = [
                TopicWord(word=feature_names[i], weight=float(topic_vec[i] / topic_vec.sum()))
                for i in top_indices
            ]
            label = ", ".join(w.word.title() for w in keywords[:4])
            topics.append(
                ExtractedTopic(
                    topic_index=idx,
                    label=label,
                    keywords=keywords,
                    relevance_score=float(topic_relevance[idx]),
                )
            )

        # Sort by relevance
        topics.sort(key=lambda t: t.relevance_score, reverse=True)
        logger.info(f"Extracted {len(topics)} topics")
        return topics

    except Exception as exc:
        logger.error(f"Topic modeling failed: {exc}")
        return []
