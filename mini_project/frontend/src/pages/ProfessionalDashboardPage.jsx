import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { tokenKey, logout } from '../auth';
import LoadingSpinner from '../components/LoadingSpinner';
import StatCard from '../components/StatCard';
import ObservationCard from '../components/ObservationCard';
import ProgressChart from '../components/ProgressChart';

function countBy(items, keyFn) {
  const counts = {};
  items.forEach((item) => {
    const key = keyFn(item);
    if (!key) return;
    counts[key] = (counts[key] || 0) + 1;
  });
  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

function ProfessionalDashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [selectedParentId, setSelectedParentId] = useState('');
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState('');
  const [analyticsError, setAnalyticsError] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const authHeader = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem(tokenKey)}` } });

  useEffect(() => {
    const token = localStorage.getItem(tokenKey);
    if (!token) { navigate('/login'); return; }

    api.get('/api/professionals/dashboard', authHeader())
      .then((res) => setSummary(res.data))
      .catch((err) => {
        if (err.response?.status === 401) { logout(); navigate('/login'); return; }
        setError(err.response?.data?.detail || 'Unable to load professional dashboard.');
      })
      .finally(() => setLoading(false));

    api.get('/api/professionals/analytics', authHeader())
      .then((res) => setAnalytics(res.data))
      .catch((err) => {
        if (err.response?.status === 401) { logout(); navigate('/login'); return; }
        setAnalyticsError(err.response?.data?.detail || 'Unable to load overall analytics.');
      });
  }, [navigate]);

  const openParent = async (parentId) => {
    setSelectedParentId(parentId);
    setSelectedChildId('');
    setProgress(null);
    try {
      const res = await api.get(`/api/professionals/parents/${parentId}/children`, authHeader());
      setChildren(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load children for this parent.');
    }
  };

  const openChild = async (childId) => {
    setSelectedChildId(childId);
    try {
      const res = await api.get(`/api/progress/${childId}`, authHeader());
      setProgress(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load child progress.');
    }
  };

  const handleCopyId = () => {
    const profId = summary?.id || summary?.professional_id;
    if (profId) {
      navigator.clipboard.writeText(profId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  if (loading) {
    return (
      <div className="page-shell dashboard-shell">
        <LoadingSpinner message="Loading professional dashboard..." />
      </div>
    );
  }

  // Safely get professional ID returned from backend
  const professionalId = summary?.id || summary?.professional_id;

  return (
    <div className="page-shell dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">DevCare</div>
        <nav className="sidebar-nav">
          <button className="nav-item active">Professional Dashboard</button>
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Professional Dashboard</p>
            <h1>My Parents & Children</h1>
            
            {/* Professional ID Display */}
            {professionalId && (
              <div style={{ marginTop: '8px', fontSize: '0.95rem' }}>
                <strong>Your Professional ID:</strong>{' '}
                <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: '4px', fontSize: '1rem', color: '#1e293b' }}>
                  #{professionalId}
                </code>
                <button 
                  onClick={handleCopyId} 
                  className="secondary-btn" 
                  style={{ marginLeft: '10px', padding: '2px 8px', fontSize: '0.8rem' }}
                >
                  {copied ? 'Copied!' : 'Copy ID'}
                </button>
              </div>
            )}
          </div>
          <button className="secondary-btn" onClick={handleLogout}>Logout</button>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className="stats-grid">
          <StatCard title="Total Parents" value={summary?.total_parents ?? 0} tone="primary" />
          <StatCard title="Total Children" value={summary?.total_children ?? 0} tone="success" />
          <StatCard title="Total Observations" value={summary?.total_observations ?? 0} />
          <StatCard
            title="Latest Observation"
            value={summary?.latest_observation_date ? new Date(summary.latest_observation_date).toLocaleDateString() : '—'}
          />
        </section>

        <section className="chart-grid">
          <div className="stat-card chart-card">
            <ProgressChart
              type="bar"
              data={(analytics?.domain_breakdown || []).map((d) => ({ domain: d.domain, count: d.count }))}
              dataKey="count"
              xKey="domain"
              title="1. Observations by domain (all students)"
            />
          </div>
          <div className="stat-card chart-card">
            <ProgressChart
              type="pie"
              data={(analytics?.domain_breakdown || []).map((d) => ({ name: d.domain, value: d.count }))}
              dataKey="value"
              labelKey="name"
              title="2. Domain share across all observations"
            />
          </div>
          <div className="stat-card chart-card">
            <ProgressChart
              type="bar"
              data={(analytics?.children || []).slice(0, 8).map((c) => ({ child: c.child_name, count: c.total_observations }))}
              dataKey="count"
              xKey="child"
              title="3. Top students by observation count"
            />
          </div>
          <div className="stat-card chart-card">
            <ProgressChart
              type="pie"
              data={countBy(analytics?.children || [], (c) => c.primary_domain)}
              dataKey="value"
              labelKey="name"
              title="4. Primary focus areas across students"
            />
          </div>
          <div className="stat-card chart-card">
            <ProgressChart
              type="bar"
              data={(summary?.parents || []).map((p) => ({ parent: p.full_name, count: p.children_count }))}
              dataKey="count"
              xKey="parent"
              title="5. Children per parent"
            />
          </div>
          <div className="stat-card chart-card">
            <ProgressChart
              type="bar"
              data={(analytics?.parent_breakdown || []).slice(0, 10).map((p) => ({ parent: p.parent_name, count: p.total_observations }))}
              dataKey="count"
              xKey="parent"
              title="6. Observations logged per parent"
            />
          </div>
          <div className="stat-card chart-card" style={{ gridColumn: '1 / -1' }}>
            <ProgressChart
              type="area"
              data={analytics?.timeline || []}
              dataKey="count"
              xKey="date"
              title="7. Observation trend across all students (by day)"
            />
          </div>
        </section>

        <section className="dashboard-summary">
          <div className="summary-card full-width">
            <h3>Students by observation volume</h3>
            {analyticsError && <p className="muted-text">{analyticsError}</p>}
            {!analyticsError && (!analytics?.children || analytics.children.length === 0) ? (
              <p className="muted-text">No observations recorded yet.</p>
            ) : (
              <div className="frequency-list">
                {analytics?.children.map((c) => (
                  <button
                    key={c.child_id}
                    className="nav-item"
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      marginBottom: '0.5rem',
                      background: '#f9fbff',
                      border: '1px solid var(--border)',
                      color: '#122b4d',
                    }}
                    onClick={() => openChild(c.child_id)}
                  >
                    <strong style={{ color: '#122b4d' }}>{c.child_name}</strong>
                    <span style={{ color: '#122b4d' }}> — {c.total_observations} obs.</span>
                    {c.primary_domain ? (
                      <span style={{ color: '#122b4d' }}> · main focus: {c.primary_domain}</span>
                    ) : ''}
                    <br />
                    <small className="muted-text">{c.parent_name} ({c.parent_email})</small>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="dashboard-summary">
          <div className="summary-card">
            <h3>My Parents</h3>
            {(!summary?.parents || summary.parents.length === 0) ? (
              <p className="muted-text">No parents associated with you yet.</p>
            ) : (
              <div className="frequency-list">
                {summary.parents.map((p) => {
                  const isSelected = String(selectedParentId) === String(p.id);
                  return (
                    <button
                      key={p.id}
                      className={`nav-item ${isSelected ? 'active' : ''}`}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        marginBottom: '0.5rem',
                        color: isSelected ? '#0f172a' : 'inherit',
                        fontWeight: isSelected ? '600' : 'normal',
                      }}
                      onClick={() => openParent(p.id)}
                    >
                      {p.full_name} — {p.children_count} child(ren)
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="summary-card">
            <h3>{selectedParentId ? "Parent's Children" : 'Select a parent'}</h3>
            {children.length === 0 ? (
              <p className="muted-text">No children to show.</p>
            ) : (
              <div className="frequency-list">
                {children.map((c) => {
                  const isSelected = String(selectedChildId) === String(c.id);
                  return (
                    <button
                      key={c.id}
                      className={`nav-item ${isSelected ? 'active' : ''}`}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        marginBottom: '0.5rem',
                        color: isSelected ? '#0f172a' : 'inherit',
                        fontWeight: isSelected ? '600' : 'normal',
                      }}
                      onClick={() => openChild(c.id)}
                    >
                      {c.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </section>

        {progress && (
          <>
            <section className="chart-grid">
              <div className="stat-card chart-card">
                <ProgressChart type="area" data={progress.timeline} dataKey="count" xKey="date" title="Observations over time" />
              </div>
              <div className="stat-card chart-card">
                <ProgressChart
                  type="pie"
                  data={progress.domain_summary.map((d) => ({ name: d.domain, value: d.count }))}
                  dataKey="value"
                  labelKey="name"
                  title="Domain summary"
                />
              </div>
            </section>

            <section className="dashboard-bottom-grid">
              <div className="summary-card full-width">
                <h3>Recent observations</h3>
                {progress.recent_observations.length === 0 ? (
                  <p className="muted-text">No recent observations.</p>
                ) : (
                  <div className="recent-list">
                    {progress.recent_observations.map((obs) => (
                      <ObservationCard key={obs.id} observation={obs} />
                    ))}
                  </div>
                )}
              </div>
            </section>
          </>
        )}

        <div className="safety-notice">
          This dashboard is intended for developmental monitoring support and is not a diagnostic tool.
        </div>
      </main>
    </div>
  );
}

export default ProfessionalDashboardPage;