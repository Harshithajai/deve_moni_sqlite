import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { tokenKey } from '../auth';
import ChildSelector from '../components/ChildSelector';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import ProgressChart from '../components/ProgressChart';

const domainOptions = [
  'Communication',
  'Social Interaction',
  'Play',
  'Cognitive / Learning',
  'Motor Skills',
  'Adaptive / Daily Living',
  'Emotional / Behavioral',
  'General Development',
];

function ProgressPage() {
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem(tokenKey);
    if (!token) {
      window.location.href = '/login';
      return;
    }

    const fetchChildren = async () => {
      try {
        const response = await api.get('/api/children', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setChildren(response.data);
        if (response.data.length > 0) {
          setSelectedChildId(String(response.data[0].id));
        }
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to load children for progress review.');
      } finally {
        setLoading(false);
      }
    };

    fetchChildren();
  }, []);

  useEffect(() => {
    if (!selectedChildId) return;

    const token = localStorage.getItem(tokenKey);
    if (!token) return;

    const fetchProgress = async () => {
      try {
        const response = await api.get(`/api/progress/${selectedChildId}`, {
          headers: { Authorization: `Bearer ${token}` },
          params: {
            domain: selectedDomain === 'all' ? undefined : selectedDomain,
            start_date: startDate || undefined,
            end_date: endDate || undefined,
          },
        });
        setProgress(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to load progress data.');
      }
    };

    fetchProgress();
  }, [selectedChildId, selectedDomain, startDate, endDate]);

  const timelineData = useMemo(() => {
    if (!progress?.timeline) return [];
    return progress.timeline.map((item) => ({
      date: item.date,
      count: item.count,
    }));
  }, [progress]);

  const domainData = useMemo(() => {
    if (!progress?.domain_summary) return [];
    return progress.domain_summary.map((item) => ({
      name: item.domain,
      value: item.count,
    }));
  }, [progress]);

  return (
    <div className="page-shell dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">DevCare</div>
        <nav className="sidebar-nav">
          <Link to="/parent/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/parent/children" className="nav-item">Children</Link>
          <Link to="/parent/observations" className="nav-item">Observations</Link>
          <Link to="/parent/history" className="nav-item">History</Link>
          <button className="nav-item active">Progress</button>
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Longitudinal Monitoring</p>
            <h1>Progress Overview</h1>
          </div>
          <Link to="/parent/dashboard" className="secondary-btn">Back to Dashboard</Link>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className="stat-card form-card progress-controls">
          <div className="split-row">
            <ChildSelector
              children={children}
              value={selectedChildId}
              onChange={(event) => setSelectedChildId(event.target.value)}
              label="Select child"
            />

            <label className="field-block">
              <span>Domain</span>
              <select value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)}>
                <option value="all">All domains</option>
                {domainOptions.map((domain) => (
                  <option key={domain} value={domain}>{domain}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="split-row">
            <label className="field-block">
              <span>Start date</span>
              <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            </label>

            <label className="field-block">
              <span>End date</span>
              <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            </label>
          </div>
        </section>

        {loading ? (
          <LoadingSpinner message="Loading progress insights..." />
        ) : !selectedChildId ? (
          <EmptyState title="No child selected" description="Choose a child to view longitudinal observation data." />
        ) : !progress || progress.total_observations === 0 ? (
          <EmptyState title="No observation data yet" description="Saved observations will appear here as trends and patterns over time." />
        ) : (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <span className="stat-label">Total observations</span>
                <strong>{progress.total_observations}</strong>
                <small>Recorded developmental observations</small>
              </div>
              <div className="stat-card">
                <span className="stat-label">Primary domain</span>
                <strong>{progress.primary_domain || 'Not available'}</strong>
                <small>Most frequently observed</small>
              </div>
              <div className="stat-card">
                <span className="stat-label">Recent observation</span>
                <strong>{progress.latest_date || 'No recent data'}</strong>
                <small>Latest recorded observation date</small>
              </div>
            </section>

            <section className="chart-grid">
              <div className="stat-card chart-card">
                <ProgressChart type="area" data={timelineData} dataKey="count" xKey="date" title="Observation count over time" />
              </div>

              <div className="stat-card chart-card">
                <ProgressChart type="pie" data={domainData} dataKey="value" labelKey="name" title="Observations by developmental domain" />
              </div>
            </section>

            <section className="chart-grid">
              <div className="stat-card chart-card">
                <ProgressChart type="bar" data={domainData} dataKey="value" xKey="name" title="Domain frequency chart" />
              </div>

              <div className="stat-card chart-card">
                <ProgressChart type="line" data={timelineData} dataKey="count" xKey="date" title="Observed activity trends" />
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default ProgressPage;
