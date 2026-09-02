"""
TextLens — Backend Test Suite

Tests: extraction, NLP, API endpoints.
Run with: cd backend && pytest tests/ -v
"""
from __future__ import annotations

import io
import pytest
from pathlib import Path

# ─── Extraction Tests ─────────────────────────────────────────────

class TestExtraction:
    def test_txt_extraction(self, tmp_path):
        from app.nlp.extractor import extract_txt
        f = tmp_path / "test.txt"
        f.write_text("The company introduced remote work in 2024. Employee productivity increased by 18%.")
        result = extract_txt(f)
        assert result.success
        assert len(result.pages) >= 1
        assert "remote work" in result.full_text.lower()

    def test_txt_empty(self, tmp_path):
        from app.nlp.extractor import extract_txt
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = extract_txt(f)
        assert not result.success
        assert "empty" in result.error.lower()

    def test_unsupported_extension(self, tmp_path):
        from app.nlp.extractor import extract_document
        f = tmp_path / "test.csv"
        f.write_text("a,b,c")
        result = extract_document(f)
        assert not result.success
        assert "unsupported" in result.error.lower()

    def test_page_numbers_preserved(self, tmp_path):
        from app.nlp.extractor import extract_txt
        # Write enough text for multiple pages
        content = " ".join(["word"] * 1200)
        f = tmp_path / "long.txt"
        f.write_text(content)
        result = extract_txt(f)
        assert result.success
        assert len(result.pages) >= 2
        assert result.pages[0].page_number == 1


# ─── Cleaning Tests ───────────────────────────────────────────────

class TestCleaning:
    def test_sentence_splitting(self):
        from app.nlp.cleaner import split_into_sentences
        text = "The company introduced remote work. Employee productivity increased by 18%. Several employees had issues."
        sents = split_into_sentences(text)
        assert len(sents) == 3

    def test_abbreviation_protection(self):
        from app.nlp.cleaner import split_into_sentences
        text = "Dr. Smith reported that Mr. Jones attended. The results were clear."
        sents = split_into_sentences(text)
        # Should NOT split on Dr. or Mr.
        assert len(sents) == 2

    def test_clean_text_normalizes_whitespace(self):
        from app.nlp.cleaner import clean_text
        dirty = "Hello   \t  world\r\nThis is   a test."
        clean = clean_text(dirty)
        assert "  " not in clean
        assert "\r" not in clean

    def test_process_pages_returns_processed_sentences(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        pages = [
            ExtractedPage(page_number=1, text="Remote work was introduced in 2024. Productivity rose by 18%."),
            ExtractedPage(page_number=2, text="Communication challenges emerged. Weekly meetings were introduced."),
        ]
        sents = process_pages(pages)
        assert len(sents) >= 4
        assert all(s.page_number in [1, 2] for s in sents)
        assert sents[0].sentence_index == 0


# ─── Entity Recognition Tests ─────────────────────────────────────

class TestEntityRecognition:
    def test_extracts_person(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.entity_recognizer import extract_entities
        pages = [ExtractedPage(page_number=1, text="Elon Musk announced Tesla's new policy in January 2024.")]
        sents = process_pages(pages)
        result = extract_entities(sents)
        labels = {e.label for e in result.entities}
        assert "PERSON" in labels or "ORG" in labels

    def test_extracts_date(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.entity_recognizer import extract_entities
        pages = [ExtractedPage(page_number=1, text="The policy was introduced on March 15, 2024.")]
        sents = process_pages(pages)
        result = extract_entities(sents)
        labels = {e.label for e in result.entities}
        assert "DATE" in labels

    def test_extracts_number(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.entity_recognizer import extract_entities
        pages = [ExtractedPage(page_number=1, text="Employee productivity increased by 18%.")]
        sents = process_pages(pages)
        result = extract_entities(sents)
        labels = {e.label for e in result.entities}
        assert "NUMBER" in labels


# ─── Sentence Scoring Tests ───────────────────────────────────────

class TestSentenceScoring:
    def _make_sents(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        text = (
            "Remote work was introduced in 2024. "
            "Employee productivity increased by 18%. "
            "Employees had difficulty communicating with teams. "
            "The company introduced weekly meetings to improve communication. "
            "The weather was sunny. "
        )
        pages = [ExtractedPage(page_number=1, text=text)]
        return process_pages(pages)

    def test_scoring_returns_all_sentences(self):
        from app.nlp.sentence_scorer import score_sentences
        sents = self._make_sents()
        scored = score_sentences(sents, [])
        assert len(scored) == len(sents)

    def test_scores_are_normalized(self):
        from app.nlp.sentence_scorer import score_sentences
        sents = self._make_sents()
        scored = score_sentences(sents, [])
        for s in scored:
            assert 0.0 <= s.importance_score <= 1.0

    def test_number_sentence_scored_higher(self):
        from app.nlp.sentence_scorer import score_sentences
        sents = self._make_sents()
        scored = score_sentences(sents, [])
        # Find the sentence with "18%"
        num_sent = next((s for s in scored if "18%" in s.text), None)
        # Find "weather" sentence
        weather_sent = next((s for s in scored if "weather" in s.text.lower()), None)
        if num_sent and weather_sent:
            assert num_sent.importance_score >= weather_sent.importance_score


# ─── Semantic Similarity Tests ────────────────────────────────────

class TestSemanticSimilarity:
    def test_similar_sentences_high_score(self):
        from app.nlp.embedder import embed_sentences, cosine_similarity
        a = "The company introduced remote work."
        b = "Employees were allowed to work from home."
        embs = embed_sentences([a, b])
        sim = cosine_similarity(embs[0], embs[1])
        assert sim > 0.50, f"Expected similarity > 0.50, got {sim:.3f}"

    def test_unrelated_sentences_low_score(self):
        from app.nlp.embedder import embed_sentences, cosine_similarity
        a = "Remote work was introduced in 2024."
        b = "The stock market crashed in 1929."
        embs = embed_sentences([a, b])
        sim = cosine_similarity(embs[0], embs[1])
        assert sim < 0.85, f"Expected similarity < 0.85, got {sim:.3f}"

    def test_similarity_matrix_shape(self):
        from app.nlp.embedder import embed_sentences, similarity_matrix
        texts = ["Sentence one.", "Sentence two.", "Sentence three."]
        embs = embed_sentences(texts)
        mat = similarity_matrix(embs)
        assert mat.shape == (3, 3)

    def test_self_similarity_is_one(self):
        from app.nlp.embedder import embed_sentences, similarity_matrix
        texts = ["This is a test sentence."]
        embs = embed_sentences(texts)
        mat = similarity_matrix(embs)
        assert abs(mat[0, 0] - 1.0) < 0.01


# ─── Relationship Detection Tests ────────────────────────────────

class TestRelationshipDetection:
    def _make_sentences(self, texts):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        pages = [ExtractedPage(page_number=1, text=" ".join(texts))]
        return process_pages(pages)

    def test_detects_cause_effect(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.embedder import embed_sentences, similarity_matrix
        from app.nlp.relationship_finder import detect_relationships

        texts = [
            "Remote work was introduced.",
            "Therefore, productivity increased by 18%.",
        ]
        pages = [ExtractedPage(page_number=1, text=" ".join(texts))]
        sents = process_pages(pages)
        embs = embed_sentences([s.text for s in sents])
        mat = similarity_matrix(embs)
        rels = detect_relationships(sents, mat, list(range(len(sents))))
        types = {r.relation_type for r in rels}
        assert "cause_effect" in types

    def test_detects_contradiction(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.embedder import embed_sentences, similarity_matrix
        from app.nlp.relationship_finder import detect_relationships

        texts = [
            "The company increased its workforce by 20 percent.",
            "The company reduced its workforce by 15 percent.",
        ]
        pages = [ExtractedPage(page_number=1, text=" ".join(texts))]
        sents = process_pages(pages)
        embs = embed_sentences([s.text for s in sents])
        mat = similarity_matrix(embs)
        rels = detect_relationships(sents, mat, list(range(len(sents))))
        types = {r.relation_type for r in rels}
        assert "contradiction" in types


# ─── Evidence Tests ───────────────────────────────────────────────

class TestEvidence:
    def test_evidence_links_to_source(self):
        from app.nlp.extractor import ExtractedPage
        from app.nlp.cleaner import process_pages
        from app.nlp.embedder import embed_sentences
        from app.nlp.evidence_linker import find_evidence

        texts = [
            "Employee productivity increased by 18%.",
            "The company reported significant productivity gains.",
            "Remote work started in 2024.",
        ]
        pages = [ExtractedPage(page_number=1, text=" ".join(texts))]
        sents = process_pages(pages)
        embs = embed_sentences([s.text for s in sents])
        links = find_evidence([0], sents, embs, min_similarity=0.3)
        assert len(links) >= 1
        assert links[0].finding_sentence_index == 0
        assert links[0].similarity_score > 0.3
