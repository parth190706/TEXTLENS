# TextLens Architecture

## Overview

TextLens uses a layered architecture:

```
Browser (React)
      │  REST/JSON
      ▼
FastAPI Backend
      │
      ├── Document Service (upload/validate/store)
      │
      └── Analysis Pipeline (NLP orchestrator)
            ├── extractor.py     → Text from files
            ├── cleaner.py       → Sentences + page tracking
            ├── entity_recognizer.py → spaCy NER
            ├── sentence_scorer.py   → TF-IDF scoring
            ├── topic_modeler.py     → LDA topics
            ├── embedder.py          → MiniLM embeddings
            ├── relationship_finder.py → Rules + similarity
            ├── evidence_linker.py    → Embedding search
            └── summarizer.py         → Centroid extraction
                    │
                    ▼
            SQLite / PostgreSQL
```

## Data Flow

```
File Upload → Validation → Disk Storage → DB Record
                                              │
                           Background Task ←─┘
                                 │
                          Text Extraction
                                 │
                         Sentence Splitting
                                 │
                      NER → Entities Table
                                 │
                      TF-IDF → Sentence scores
                                 │
                      LDA → Topics Table
                                 │
                      MiniLM → Embeddings (in-memory)
                                 │
                   Similarity Matrix → Relationships Table
                                 │
                   Embedding search → Evidence Table
                                 │
                   Centroid → Summary → Analysis Table
                                 │
                         Status: completed
```

## Key Design Decisions

- **Async processing**: Analysis runs as a FastAPI BackgroundTask, polling via `/status`
- **Lazy model loading**: spaCy and MiniLM are loaded once on first use
- **Source traceability**: Every entity, finding, relationship, and evidence link stores `page_number` and `sentence_id`
- **No black-box AI**: All analysis steps use interpretable algorithms
