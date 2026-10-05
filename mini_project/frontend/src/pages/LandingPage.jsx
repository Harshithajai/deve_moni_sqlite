import { Link } from 'react-router-dom';

function LandingPage() {
  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-group">
          <div className="brand-mark">D</div>
          <div>
            <div className="brand-title">DevCare</div>
            <div className="brand-subtitle">Developmental Monitoring &amp; Caregiver Assistance</div>
          </div>
        </div>
        <nav className="topnav">
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
        </nav>
      </header>

      <main className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Evidence-grounded support</span>
          <h1>Caregiver tools for developmental monitoring</h1>
          <p>
            DevCare helps families and care teams track developmental milestones with a secure,
            modern monitoring platform.
          </p>
          <div className="cta-row">
            <Link className="primary-btn" to="/register">
              Get Started
            </Link>
            <Link className="secondary-btn" to="/login">
              Sign In
            </Link>
          </div>
        </div>

        <div className="hero-card">
          <div className="card-row">
            <span className="stat-label">Monitoring status</span>
            <span className="badge success">Secure</span>
          </div>
          <h3>Developmental monitoring dashboard</h3>
          <ul>
            <li>Track caregiver data securely</li>
            <li>Review status over time</li>
            <li>Support informed caregiving decisions</li>
          </ul>
        </div>
      </main>

      <div className="notice-box">
        "This application is intended for developmental monitoring and caregiver support. It is not a diagnostic tool or a substitute for professional medical advice."
      </div>
    </div>
  );
}

export default LandingPage;
