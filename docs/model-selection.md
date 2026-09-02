# Model Selection

## Embedding Model: `all-MiniLM-L6-v2`

**Source**: Hugging Face — `sentence-transformers/all-MiniLM-L6-v2`
**License**: Apache 2.0
**Size**: ~80MB
**Why**: Best balance of speed and quality for semantic similarity. Runs on CPU. 384-dimension output.

## NER Model: `en_core_web_sm`

**Source**: spaCy
**License**: MIT
**Size**: ~12MB
**Why**: Fast, accurate, offline. Recognizes PERSON, ORG, GPE, DATE, CARDINAL, MONEY, PERCENT.

## Topic Model: LDA (scikit-learn)

**Why**: No GPU needed. Interpretable keyword output. Works well for 5-500 sentence documents.
Configured with `n_components=5`, `max_iter=20`.

## Sentence Scoring: TF-IDF (scikit-learn)

**Why**: Established, fast, interpretable. Combined with entity density and positional signals.

## Summary: Centroid-based Extraction

**Why**: Faithful to source text — never generates text not in the document.
Selects sentences closest (cosine similarity) to the document embedding centroid.

## Relationship Detection: Rule-based + Similarity

**Why**: Interpretable, explainable. Users can see exactly which cue phrase triggered a relationship.
Semantic similarity (cosine ≥ 0.80) supplements rule-based detection.
