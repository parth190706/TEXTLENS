// TextLens API client
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export interface Document {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  page_count?: number;
  sentence_count?: number;
  created_at: string;
  error_message?: string;
}

export interface AnalysisStatus {
  document_id: string;
  status: string;
  error_message?: string;
  page_count?: number;
  sentence_count?: number;
}

export interface Finding {
  id: string;
  rank: number;
  text: string;
  importance_score: number;
  page_number?: number;
  reason?: string;
}

export interface EntityItem {
  id: string;
  text: string;
  label: string;
  normalized?: string;
  page_number?: number;
  count: number;
}

export interface EntitiesResponse {
  document_id: string;
  people: EntityItem[];
  organizations: EntityItem[];
  locations: EntityItem[];
  dates: EntityItem[];
  numbers: EntityItem[];
  other: EntityItem[];
}

export interface TopicKeyword {
  word: string;
  weight: number;
}

export interface Topic {
  id: string;
  label: string;
  keywords: TopicKeyword[];
  relevance_score: number;
}

export interface Relationship {
  id: string;
  source_text: string;
  target_text: string;
  source_page?: number;
  target_page?: number;
  relation_type: 'cause_effect' | 'problem_solution' | 'support' | 'similar' | 'contradiction';
  confidence: number;
  explanation?: string;
  cue_phrase?: string;
}

export interface Evidence {
  id: string;
  finding_text: string;
  evidence_text: string;
  page_number?: number;
  similarity_score: number;
}

export interface AnalysisResponse {
  document_id: string;
  summary?: string;
  overall_interpretation?: string;
  processing_duration_seconds?: number;
  key_findings: Finding[];
  entities: EntitiesResponse;
  topics: Topic[];
  relationships: Relationship[];
  evidence: Evidence[];
  contradictions: Relationship[];
  created_at?: string;
}

// ── API Functions ──────────────────────────────────────────────────

export const uploadDocument = async (file: File): Promise<Document> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<Document>('/api/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const triggerAnalysis = async (docId: string): Promise<void> => {
  await api.post(`/api/documents/${docId}/analyze`);
};

export const getAnalysisStatus = async (docId: string): Promise<AnalysisStatus> => {
  const res = await api.get<AnalysisStatus>(`/api/documents/${docId}/status`);
  return res.data;
};

export const getAnalysis = async (docId: string): Promise<AnalysisResponse> => {
  const res = await api.get<AnalysisResponse>(`/api/documents/${docId}/analysis`);
  return res.data;
};

export const listDocuments = async (): Promise<Document[]> => {
  const res = await api.get<Document[]>('/api/documents');
  return res.data;
};

export default api;
