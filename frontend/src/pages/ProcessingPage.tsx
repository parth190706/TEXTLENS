import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAnalysisStatus } from '../api/client';

const STAGES = [
  { key: 'extract', label: 'Reading document', desc: 'Extracting text from file' },
  { key: 'clean', label: 'Preparing text', desc: 'Cleaning and splitting sentences' },
  { key: 'entities', label: 'Finding important information', desc: 'Entity recognition (NER)' },
  { key: 'score', label: 'Scoring content', desc: 'Importance & relevance scoring' },
  { key: 'topics', label: 'Identifying topics', desc: 'Topic modeling (LDA)' },
  { key: 'embed', label: 'Understanding content', desc: 'Semantic embeddings' },
  { key: 'relate', label: 'Finding relationships', desc: 'Cause-effect, contradictions' },
  { key: 'evidence', label: 'Linking evidence', desc: 'Tracing findings to source' },
  { key: 'summary', label: 'Generating report', desc: 'Summary & interpretation' },
];

function estimateStage(elapsedMs: number, totalStages: number): number {
  // Estimate progress based on elapsed time (stages take ~3-5s each on CPU)
  const avgPerStage = 5000;
  return Math.min(Math.floor(elapsedMs / avgPerStage), totalStages - 1);
}

export default function ProcessingPage() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [estimatedStage, setEstimatedStage] = useState(0);
  const startRef = useRef(Date.now());
  const intervalRef = useRef<ReturnType<typeof window.setInterval> | undefined>(undefined);

  useEffect(() => {
    if (!docId) return;

    const poll = async () => {
      try {
        const status = await getAnalysisStatus(docId);
        const elapsed = Date.now() - startRef.current;
        setEstimatedStage(estimateStage(elapsed, STAGES.length));

        if (status.status === 'completed') {
          clearInterval(intervalRef.current);
          navigate(`/results/${docId}`);
        } else if (status.status === 'failed') {
          clearInterval(intervalRef.current);
          setError(status.error_message || 'Analysis failed. Please try again.');
        }
      } catch (e: any) {
        setError('Failed to reach the server. Is the backend running?');
        clearInterval(intervalRef.current);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2500);
    return () => clearInterval(intervalRef.current);
  }, [docId, navigate]);

  return (
    <div className="page">
      <Navbar />
      <div style={{ maxWidth: 600, margin: '60px auto', padding: '0 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 16 }}>⚙️</div>
          <h2 style={{ color: 'var(--color-text-primary)', marginBottom: 8 }}>Analyzing Document</h2>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            TextLens is processing your document. This may take a moment.
          </p>
        </div>

        {error && (
          <div className="alert alert-error">⚠️ {error}</div>
        )}

        <div className="progress-steps">
          {STAGES.map((stage, idx) => {
            let state: 'done' | 'active' | 'pending';
            if (idx < estimatedStage) state = 'done';
            else if (idx === estimatedStage) state = 'active';
            else state = 'pending';

            return (
              <div key={stage.key} className={`step ${state}`}>
                <div className="step-icon">
                  {state === 'done' ? '✅' : state === 'active' ? '⚡' : '○'}
                </div>
                <div>
                  <div className="step-label">{stage.label}</div>
                  <div className="step-status">{stage.desc}</div>
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ textAlign: 'center', marginTop: 32, color: 'var(--color-text-muted)', fontSize: '0.82rem' }}>
          Progress estimate — actual stages run in the backend
        </div>
      </div>
    </div>
  );
}
