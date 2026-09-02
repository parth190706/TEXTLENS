# TextLens 🔍

**Intelligent Document Analysis — Structured, Traceable, Explainable**

TextLens is an open-source document analysis application that transforms uploaded PDF, DOCX, and TXT files into structured, actionable insights. It extracts named entities, detects relationships, links evidence to source text, identifies contradictions, and produces a faithful summary — all without relying on paid AI APIs.

---

## Problem Statement

Existing document analysis tools either:
- Return black-box AI responses with no traceability
- Require expensive API subscriptions
- Provide generic summaries without structured relationship analysis

TextLens solves this by building a modular, explainable NLP pipeline where every finding is traceable to its source sentence and page.

---

## Features

| Feature | Description |
|---|---|
| 📄 **Multi-format Support** | PDF, DOCX, TXT with page tracking |
| 🏷️ **Entity Extraction** | People, organizations, locations, dates, numbers |
| 🔗 **Relationship Detection** | Cause-effect, problem-solution, support, similar, contradiction |
| 🔍 **Evidence Linking** | Every finding linked to source sentence and page |
| ⚡ **Contradiction Detection** | Semantically similar statements with opposing polarity |
| 💡 **Topic Modeling** | LDA-based topic identification |
| 📊 **Importance Scoring** | TF-IDF + entity density + position scoring |
| 🧠 **Semantic Similarity** | Sentence embeddings (MiniLM) for meaning-based comparison |
| 📋 **Extractive Summary** | Centroid-based summary faithful to source text |
| 🎨 **Professional UI** | React + TypeScript dashboard with 7 analysis tabs |
| 🔒 **Security** | File validation, magic-byte checking, size limits |
| 🐳 **Docker Support** | One-command setup |

---

## Architecture

```
Frontend (React + Vite)
        │  HTTP/REST
        ▼
Backend (FastAPI + Python)
   ├── Document Service     ← File validation, storage
   └── Analysis Pipeline
        ├── 1. Text Extraction (PyMuPDF / python-docx)
        ├── 2. Cleaning + Sentence Splitting
        ├── 3. Entity Recognition (spaCy en_core_web_sm)
        ├── 4. Importance Scoring (TF-IDF)
        ├── 5. Topic Modeling (LDA)
        ├── 6. Sentence Embeddings (all-MiniLM-L6-v2)
        ├── 7. Relationship Detection
        ├── 8. Contradiction Detection
        ├── 9. Evidence Linking
        └── 10. Extractive Summary
              │
              ▼
        Database (SQLite / PostgreSQL)
```

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Backend | FastAPI | 0.111 |
| ORM | SQLAlchemy (async) | 2.0 |
| Database (dev) | SQLite + aiosqlite | — |
| Database (prod) | PostgreSQL | 15+ |
| NER | spaCy | 3.7 |
| Embeddings | sentence-transformers | 3.0 |
| Embedding Model | all-MiniLM-L6-v2 | ~80MB |
| Topics | scikit-learn LDA | 1.5 |
| PDF | PyMuPDF | 1.24 |
| DOCX | python-docx | 1.1 |
| Frontend | React + TypeScript | 18 + 5 |
| Build Tool | Vite | 5 |
| HTTP Client | Axios | — |

---

## Project Structure

```
SEM5/
├── backend/
│   ├── app/
│   │   ├── api/          # REST route handlers
│   │   ├── core/         # Config + logging
│   │   ├── db/           # SQLAlchemy models + session
│   │   ├── nlp/          # All NLP components
│   │   │   ├── extractor.py
│   │   │   ├── cleaner.py
│   │   │   ├── entity_recognizer.py
│   │   │   ├── sentence_scorer.py
│   │   │   ├── topic_modeler.py
│   │   │   ├── embedder.py
│   │   │   ├── relationship_finder.py
│   │   │   ├── evidence_linker.py
│   │   │   └── summarizer.py
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── main.py
│   ├── data/             # Sample evaluation documents
│   ├── tests/            # pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/          # TypeScript API client
│       ├── components/   # Navbar, UploadZone
│       └── pages/        # HomePage, ProcessingPage, ResultsPage
├── docs/                 # Documentation
├── docker-compose.yml
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### 1. Clone the repository

```bash
git clone <repo-url>
cd SEM5
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required)
python -m spacy download en_core_web_sm

# Configure environment
copy .env.example .env
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

---

## Environment Setup

Copy `backend/.env.example` to `backend/.env` and adjust if needed:

```env
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./textlens.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
SPACY_MODEL=en_core_web_sm
EMBEDDING_MODEL=all-MiniLM-L6-v2
ALLOWED_ORIGINS=http://localhost:5173
```

> **Note:** The `all-MiniLM-L6-v2` embedding model (~80MB) is downloaded automatically from Hugging Face on first run.

---

## Running the Application

### Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
Interactive API docs: `http://localhost:8000/api/docs`

### Frontend

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`

---

## Docker Setup

```bash
docker compose up --build
```

This starts both the backend and frontend.

---

## Testing

```bash
cd backend
pytest tests/ -v
```

Test coverage:
- File extraction (PDF, DOCX, TXT, empty, unsupported)
- Text cleaning and sentence splitting
- Entity recognition
- Sentence scoring
- Semantic similarity
- Relationship detection
- Evidence linking
- API endpoints

---

## API Documentation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents` | Upload document |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Document details |
| POST | `/api/documents/{id}/analyze` | Trigger analysis |
| GET | `/api/documents/{id}/status` | Poll analysis status |
| GET | `/api/documents/{id}/analysis` | Full analysis result |
| GET | `/api/documents/{id}/findings` | Key findings |
| GET | `/api/documents/{id}/entities` | Extracted entities |
| GET | `/api/documents/{id}/topics` | Topics |
| GET | `/api/documents/{id}/relationships` | Relationships |
| GET | `/api/documents/{id}/evidence` | Evidence links |

Interactive docs available at `/api/docs`.

---

## Example Workflow

1. Start both backend and frontend
2. Navigate to `http://localhost:5173`
3. Upload `backend/data/sample_01.txt` (remote work scenario)
4. Wait for analysis (~30–60 seconds on CPU, first run downloads models)
5. Explore:
   - **Summary** — concise document overview
   - **Key Findings** — top 10 important sentences with scores
   - **Entities** — people, organizations, dates, numbers
   - **Topics** — major themes
   - **Relationships** — cause-effect and problem-solution chains
   - **Evidence** — each finding linked to source text and page
   - **Contradictions** — possibly conflicting statements

---

## Limitations

- First run downloads ~80MB (MiniLM model) from Hugging Face — requires internet
- CPU inference for embeddings: ~5–30 seconds per document depending on length
- Topic modeling requires at least 5+ sentences
- Relationship detection is heuristic-based — some false positives are expected
- Contradiction detection uses polarity analysis — nuanced contradictions may be missed
- DOCX page numbers are approximated by section headings, not actual pages

---

## Future Improvements

- GPU acceleration support (CUDA)
- PostgreSQL production deployment guide
- User authentication and document history
- Export analysis as PDF report
- More sophisticated contradiction detection using NLI models
- Multi-document comparison
- Batch processing API

---

## Model & Dependency Licenses

| Model/Library | License | Source |
|---|---|---|
| spaCy `en_core_web_sm` | MIT | spacy.io |
| `all-MiniLM-L6-v2` | Apache 2.0 | Hugging Face |
| sentence-transformers | Apache 2.0 | sbert.net |
| PyMuPDF | AGPL-3.0 | pymupdf.readthedocs.io |
| python-docx | MIT | python-docx.readthedocs.io |
| scikit-learn | BSD-3 | scikit-learn.org |
| FastAPI | MIT | fastapi.tiangolo.com |
| SQLAlchemy | MIT | sqlalchemy.org |
| React | MIT | react.dev |

---

## Contributors

- TextLens Engineering Team — VIT SEM5 EDI Project

---

## License

MIT License — See LICENSE file for details.
