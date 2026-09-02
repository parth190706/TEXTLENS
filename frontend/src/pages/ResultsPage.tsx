import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAnalysis, type AnalysisResponse, type Relationship } from '../api/client';

type Tab = 'summary' | 'findings' | 'entities' | 'topics' | 'relationships' | 'evidence' | 'contradictions';

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'summary', label: 'Summary', icon: '📋' },
  { key: 'findings', label: 'Key Findings', icon: '🏆' },
  { key: 'entities', label: 'Entities', icon: '🏷️' },
  { key: 'topics', label: 'Topics', icon: '💡' },
  { key: 'relationships', label: 'Relationships', icon: '🔗' },
  { key: 'evidence', label: 'Evidence', icon: '🔍' },
  { key: 'contradictions', label: 'Contradictions', icon: '⚡' },
];

function RelTypeLabel({ type }: { type: string }) {
  const map: Record<string, { label: string; color: string }> = {
    cause_effect: { label: 'Cause → Effect', color: '#6378ff' },
    problem_solution: { label: 'Problem → Solution', color: '#38d9a9' },
    support: { label: 'Support', color: '#ffd166' },
    similar: { label: 'Similar', color: '#8892b0' },
    contradiction: { label: 'Contradiction', color: '#ff6b6b' },
  };
  const info = map[type] || { label: type, color: '#8892b0' };
  return (
    <span className="rel-type-badge" style={{ background: `${info.color}20`, color: info.color, border: `1px solid ${info.color}40` }}>
      {info.label}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="score-bar">
      <div className="score-bar-fill" style={{ width: `${Math.round(score * 100)}%` }} />
    </div>
  );
}

export default function ResultsPage() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('summary');

  useEffect(() => {
    if (!docId) return;
    getAnalysis(docId)
      .then(data => { setAnalysis(data); setLoading(false); })
      .catch(e => {
        const msg = e?.response?.data?.detail || e.message || 'Failed to load analysis.';
        if (e?.response?.status === 422) {
          navigate(`/processing/${docId}`);
          return;
        }
        setError(msg);
        setLoading(false);
      });
  }, [docId, navigate]);

  if (loading) {
    return (
      <div className="page">
        <Navbar />
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', gap: 16 }}>
          <span className="spinner" />
          <span style={{ color: 'var(--color-text-secondary)' }}>Loading analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <Navbar />
        <div style={{ maxWidth: 500, margin: '80px auto', padding: '0 24px' }}>
          <div className="alert alert-error">⚠️ {error}</div>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const entities = analysis.entities;
  const totalFindings = analysis.key_findings.length;
  const totalRels = analysis.relationships.length;
  const totalContradictions = analysis.contradictions.length;

  return (
    <div className="page">
      <Navbar />

      {/* Results layout */}
      <div className="results-layout">

        {/* Sidebar */}
        <aside className="results-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-label">Document</div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Status</span>
              <span className="badge badge-success">✓ Analyzed</span>
            </div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Duration</span>
              <span className="sidebar-stat-value">
                {analysis.processing_duration_seconds?.toFixed(1)}s
              </span>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-label">Statistics</div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Findings</span>
              <span className="sidebar-stat-value">{totalFindings}</span>
            </div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Topics</span>
              <span className="sidebar-stat-value">{analysis.topics.length}</span>
            </div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Relationships</span>
              <span className="sidebar-stat-value">{totalRels}</span>
            </div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Evidence Links</span>
              <span className="sidebar-stat-value">{analysis.evidence.length}</span>
            </div>
            <div className="sidebar-stat">
              <span className="sidebar-stat-label">Contradictions</span>
              <span className="sidebar-stat-value">{totalContradictions}</span>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-label">Entities Found</div>
            {[
              { label: 'People', count: entities.people.length },
              { label: 'Organizations', count: entities.organizations.length },
              { label: 'Locations', count: entities.locations.length },
              { label: 'Dates', count: entities.dates.length },
              { label: 'Numbers', count: entities.numbers.length },
            ].map(e => (
              <div key={e.label} className="sidebar-stat">
                <span className="sidebar-stat-label">{e.label}</span>
                <span className="sidebar-stat-value">{e.count}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* Main content */}
        <main className="results-main">

          {/* Tabs */}
          <div className="tabs">
            {TABS.map(t => (
              <button
                key={t.key}
                className={`tab ${activeTab === t.key ? 'active' : ''}`}
                onClick={() => setActiveTab(t.key)}
              >
                {t.icon} {t.label}
                {t.key === 'contradictions' && totalContradictions > 0 && (
                  <span className="badge badge-danger" style={{ marginLeft: 6, fontSize: '0.65rem', padding: '2px 6px' }}>
                    {totalContradictions}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div>
              <div className="section-header">
                <div className="section-title">📋 Document Summary</div>
                <div className="section-desc">Extractive summary — faithful to source text</div>
              </div>
              <div className="summary-block">
                {analysis.summary || 'No summary available.'}
              </div>
              {analysis.overall_interpretation && (
                <div className="interpretation-block">
                  <strong style={{ color: 'var(--color-text-primary)' }}>Overall Interpretation: </strong>
                  {analysis.overall_interpretation}
                </div>
              )}
            </div>
          )}

          {/* Key Findings Tab */}
          {activeTab === 'findings' && (
            <div>
              <div className="section-header">
                <div className="section-title">🏆 Key Findings</div>
                <div className="section-desc">Sentences ranked by importance — TF-IDF + entity density + position</div>
              </div>
              {analysis.key_findings.length === 0 ? (
                <div className="empty-state"><span className="empty-state-icon">📭</span>No findings available</div>
              ) : (
                analysis.key_findings.map(f => (
                  <div key={f.id} className="finding-card">
                    <div className="finding-rank">#{f.rank}</div>
                    <div className="finding-content">
                      <div className="finding-text">"{f.text}"</div>
                      <div className="finding-meta">
                        <span className="finding-score">Score: {(f.importance_score * 100).toFixed(0)}%</span>
                        {f.page_number && <span className="finding-page">Page {f.page_number}</span>}
                        {f.reason && <span className="finding-reason">{f.reason}</span>}
                      </div>
                      <ScoreBar score={f.importance_score} />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Entities Tab */}
          {activeTab === 'entities' && (
            <div>
              <div className="section-header">
                <div className="section-title">🏷️ Extracted Entities</div>
                <div className="section-desc">Named entities identified using spaCy NER</div>
              </div>
              {[
                { key: 'people', label: '👤 People', chipClass: 'person', items: entities.people },
                { key: 'organizations', label: '🏢 Organizations', chipClass: 'org', items: entities.organizations },
                { key: 'locations', label: '📍 Locations', chipClass: 'loc', items: entities.locations },
                { key: 'dates', label: '📅 Dates', chipClass: 'date', items: entities.dates },
                { key: 'numbers', label: '🔢 Numbers', chipClass: 'number', items: entities.numbers },
              ].map(section => (
                section.items.length > 0 && (
                  <div key={section.key} className="entity-section">
                    <div className="entity-section-title">{section.label}</div>
                    <div className="entity-chips">
                      {section.items.map(e => (
                        <span key={e.id} className={`entity-chip ${section.chipClass}`} title={`Page ${e.page_number || '?'}`}>
                          {e.text}
                          {e.count > 1 && <span className="count">×{e.count}</span>}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              ))}
              {Object.values(entities).every(v => Array.isArray(v) ? v.length === 0 : true) && (
                <div className="empty-state"><span className="empty-state-icon">🏷️</span>No entities found</div>
              )}
            </div>
          )}

          {/* Topics Tab */}
          {activeTab === 'topics' && (
            <div>
              <div className="section-header">
                <div className="section-title">💡 Topics</div>
                <div className="section-desc">Major themes identified using LDA topic modeling</div>
              </div>
              {analysis.topics.length === 0 ? (
                <div className="empty-state"><span className="empty-state-icon">💡</span>No topics identified</div>
              ) : (
                <div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 32 }}>
                    {analysis.topics.map(t => (
                      <span key={t.id} className="topic-chip">
                        {t.label}
                        <span className="topic-score">{(t.relevance_score * 100).toFixed(0)}%</span>
                      </span>
                    ))}
                  </div>
                  {analysis.topics.map(t => (
                    <div key={t.id} className="card" style={{ marginBottom: 16 }}>
                      <div className="card-title" style={{ marginBottom: 12 }}>{t.label}</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {t.keywords.map(kw => (
                          <span key={kw.word} style={{
                            padding: '3px 10px',
                            borderRadius: 100,
                            background: 'var(--color-surface-3)',
                            fontSize: '0.78rem',
                            color: 'var(--color-text-secondary)',
                            border: '1px solid var(--color-border)',
                            opacity: 0.5 + kw.weight * 5,
                          }}>
                            {kw.word}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Relationships Tab */}
          {activeTab === 'relationships' && (
            <div>
              <div className="section-header">
                <div className="section-title">🔗 Relationships</div>
                <div className="section-desc">Cause-effect, problem-solution, and supporting relationships</div>
              </div>
              {analysis.relationships.length === 0 ? (
                <div className="empty-state"><span className="empty-state-icon">🔗</span>No relationships detected</div>
              ) : (
                analysis.relationships.map(r => (
                  <RelationshipCard key={r.id} rel={r} />
                ))
              )}
            </div>
          )}

          {/* Evidence Tab */}
          {activeTab === 'evidence' && (
            <div>
              <div className="section-header">
                <div className="section-title">🔍 Evidence Links</div>
                <div className="section-desc">Each finding traced to its supporting source sentence</div>
              </div>
              {analysis.evidence.length === 0 ? (
                <div className="empty-state"><span className="empty-state-icon">🔍</span>No evidence links available</div>
              ) : (
                analysis.evidence.map(ev => (
                  <div key={ev.id} className="evidence-card">
                    <div className="evidence-finding">📌 {ev.finding_text}</div>
                    <div className="evidence-source">"{ev.evidence_text}"</div>
                    <div className="evidence-meta">
                      <span className="evidence-similarity">
                        Similarity: {(ev.similarity_score * 100).toFixed(0)}%
                      </span>
                      {ev.page_number && (
                        <span className="evidence-page">Page {ev.page_number}</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Contradictions Tab */}
          {activeTab === 'contradictions' && (
            <div>
              <div className="section-header">
                <div className="section-title">⚡ Possible Contradictions</div>
                <div className="section-desc">
                  Statements with similar topics but opposing polarity — may indicate conflicting information.
                  These are flagged for human review; not guaranteed contradictions.
                </div>
              </div>
              {analysis.contradictions.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">✅</span>
                  No contradictions detected
                </div>
              ) : (
                analysis.contradictions.map(c => (
                  <div key={c.id} className="contradiction-card">
                    <div className="contradiction-header">⚠️ Possible Contradiction</div>
                    <div className="contradiction-statements">
                      <div className="contradiction-stmt">"{c.source_text}"</div>
                      <div className="contradiction-vs">VS</div>
                      <div className="contradiction-stmt">"{c.target_text}"</div>
                    </div>
                    <div className="contradiction-explanation">
                      {c.explanation} · Confidence: {(c.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function RelationshipCard({ rel }: { rel: Relationship }) {
  const arrowMap: Record<string, string> = {
    cause_effect: '↓',
    problem_solution: '→',
    support: '↑',
    similar: '↔',
    contradiction: '≠',
  };

  return (
    <div className="relationship-item">
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 12 }}>
        <RelTypeLabel type={rel.relation_type} />
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
          Confidence: {(rel.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <div className="relationship-nodes">
        <div className="rel-node source">
          {rel.source_text}
          {rel.source_page && <span style={{ marginLeft: 8, fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>p.{rel.source_page}</span>}
        </div>
        <div className="rel-arrow">
          <div className="rel-arrow-line" />
          <div style={{ fontSize: '1.2rem', marginLeft: 8, color: 'var(--color-text-muted)' }}>
            {arrowMap[rel.relation_type] || '↓'}
          </div>
          <div className="rel-arrow-line" />
        </div>
        <div className="rel-node target">
          {rel.target_text}
          {rel.target_page && <span style={{ marginLeft: 8, fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>p.{rel.target_page}</span>}
        </div>
      </div>
      {rel.explanation && (
        <div style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
          {rel.explanation}
          {rel.cue_phrase && <span style={{ marginLeft: 8, background: 'var(--color-primary-glow)', padding: '1px 6px', borderRadius: 4, fontStyle: 'normal' }}>"{rel.cue_phrase}"</span>}
        </div>
      )}
    </div>
  );
}
