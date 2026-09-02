import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProcessingPage from './pages/ProcessingPage';
import ResultsPage from './pages/ResultsPage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/processing/:docId" element={<ProcessingPage />} />
        <Route path="/results/:docId" element={<ResultsPage />} />
        <Route path="*" element={
          <div style={{ textAlign: 'center', padding: 80, color: 'var(--color-text-secondary)' }}>
            <div style={{ fontSize: '3rem', marginBottom: 16 }}>404</div>
            <a href="/" style={{ color: 'var(--color-primary-light)' }}>← Back to TextLens</a>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}
