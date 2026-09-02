# Database Schema

## Tables

### documents
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| filename | VARCHAR | Stored filename (UUID-prefixed, sanitized) |
| original_filename | VARCHAR | User's original filename |
| file_type | VARCHAR | pdf / docx / txt |
| file_size | INT | Bytes |
| upload_path | VARCHAR | Full path to stored file |
| status | ENUM | uploaded / processing / completed / failed |
| error_message | TEXT | Error detail if failed |
| page_count | INT | Extracted page count |
| sentence_count | INT | Total sentences extracted |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### sentences
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK → documents | |
| page_id | FK → document_pages | |
| sentence_index | INT | Global 0-based index in document |
| page_number | INT | Source page (1-indexed) |
| section | VARCHAR | Section heading if available |
| text | TEXT | Cleaned sentence text |
| importance_score | FLOAT | TF-IDF-based importance (0–1) |

### entities
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK | |
| sentence_id | FK → sentences | |
| text | VARCHAR | Entity text |
| label | ENUM | PERSON / ORG / LOC / DATE / NUMBER |
| count | INT | Frequency in document |
| page_number | INT | First occurrence page |

### findings
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK | |
| sentence_id | FK → sentences | |
| rank | INT | 1 = most important |
| text | TEXT | Sentence text |
| importance_score | FLOAT | |
| page_number | INT | |
| reason | TEXT | Human-readable explanation |

### relationships
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK | |
| source_sentence_id | FK → sentences | |
| target_sentence_id | FK → sentences | |
| relation_type | ENUM | cause_effect / problem_solution / support / similar / contradiction |
| confidence | FLOAT | 0–1 |
| explanation | TEXT | Why this relationship was detected |
| cue_phrase | VARCHAR | Triggering cue word/phrase |

### evidence_links
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK | |
| finding_id | FK → findings | |
| sentence_id | FK → sentences | Supporting sentence |
| similarity_score | FLOAT | Cosine similarity |
| page_number | INT | Page of supporting sentence |

### analyses
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| document_id | FK (unique) | |
| summary | TEXT | Extractive summary |
| overall_interpretation | TEXT | Structured interpretation |
| processing_duration_seconds | FLOAT | |
| meta | JSON | Statistics dict |

## Traceability Chain

```
Finding (rank, text, score)
   └── sentence_id → Sentence (page_number, section)
         └── page_id → DocumentPage (raw_text)
               └── document_id → Document (filename)

EvidenceLink (similarity_score)
   ├── finding_id → Finding
   └── sentence_id → Sentence (page_number)
```
