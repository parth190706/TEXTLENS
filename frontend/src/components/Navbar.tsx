import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon">🔍</div>
          TextLens
        </Link>
        <div className="navbar-actions">
          {!isHome && (
            <Link to="/" className="btn btn-secondary">
              ↑ Upload New
            </Link>
          )}
          <a
            href="/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-ghost"
          >
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}
