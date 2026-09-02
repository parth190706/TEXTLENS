import Navbar from '../components/Navbar';
import UploadZone from '../components/UploadZone';

export default function HomePage() {
  return (
    <div className="page">
      <Navbar />
      <div className="page-hero">
        <div className="hero-eyebrow">✦ Intelligent Document Analysis</div>
        <h1 className="hero-title">Understand Your Documents</h1>
        <p className="hero-sub">
          Upload any PDF, DOCX, or TXT file. TextLens extracts entities, detects relationships,
          tracks evidence, and surfaces insights — all traceable to the source.
        </p>

        <div style={{ maxWidth: 560, margin: '0 auto' }}>
          <UploadZone />
        </div>

        <div style={{ marginTop: 48, display: 'flex', justifyContent: 'center', gap: 32, flexWrap: 'wrap' }}>
          {[
            { icon: '🏷️', label: 'Entity Extraction', desc: 'People, orgs, dates, numbers' },
            { icon: '🔗', label: 'Relationship Detection', desc: 'Cause-effect, problem-solution' },
            { icon: '🔍', label: 'Evidence Tracking', desc: 'Every finding traced to source' },
            { icon: '⚡', label: 'Semantic Analysis', desc: 'Meaning-based, not keyword' },
          ].map(f => (
            <div key={f.label} style={{
              textAlign: 'center',
              padding: '16px 20px',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              minWidth: 140,
              maxWidth: 180,
            }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>{f.icon}</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>{f.label}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
