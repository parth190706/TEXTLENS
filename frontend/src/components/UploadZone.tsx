import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadDocument, triggerAnalysis } from '../api/client';

const ALLOWED = ['.pdf', '.docx', '.txt'];
const MAX_MB = 50;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadZone() {
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported file type. Allowed: PDF, DOCX, TXT`;
    if (file.size === 0) return 'File is empty.';
    if (file.size > MAX_MB * 1024 * 1024) return `File exceeds ${MAX_MB}MB limit.`;
    return '';
  };

  const handleFile = useCallback((file: File) => {
    const err = validateFile(file);
    if (err) { setError(err); return; }
    setError('');
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError('');
    try {
      const doc = await uploadDocument(selectedFile);
      await triggerAnalysis(doc.id);
      navigate(`/processing/${doc.id}`);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Upload failed.';
      setError(msg);
      setLoading(false);
    }
  };

  return (
    <div>
      <div
        className={`upload-zone ${dragging ? 'drag-over' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !selectedFile && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleChange}
          style={{ display: 'none' }}
          id="file-upload"
        />
        <span className="upload-icon">{dragging ? '📂' : selectedFile ? '📄' : '☁️'}</span>

        {selectedFile ? (
          <>
            <div className="upload-title">{selectedFile.name}</div>
            <div className="upload-subtitle">{formatBytes(selectedFile.size)} · Ready to analyze</div>
            <button
              className="btn btn-ghost"
              onClick={e => { e.stopPropagation(); setSelectedFile(null); }}
              style={{ marginTop: 8 }}
            >
              Change file
            </button>
          </>
        ) : (
          <>
            <div className="upload-title">Drop your document here</div>
            <div className="upload-subtitle">or click to browse your files</div>
          </>
        )}

        <div className="supported-types">
          {ALLOWED.map(ext => (
            <span key={ext} className="type-badge">{ext.toUpperCase().replace('.', '')}</span>
          ))}
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginTop: 16 }}>
          ⚠️ {error}
        </div>
      )}

      {selectedFile && (
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <button
            id="analyze-btn"
            className="btn btn-primary btn-lg"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? (
              <><span className="spinner" style={{ width: 18, height: 18 }} /> Uploading...</>
            ) : (
              '🔍 Analyze Document'
            )}
          </button>
        </div>
      )}
    </div>
  );
}
