import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { tokenKey } from '../auth';

function HistoryPage() {
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('all');
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [selectedDate, setSelectedDate] = useState('');
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem(tokenKey);
      if (!token) {
        window.location.href = '/login';
        return;
      }

      try {
        const childrenResponse = await api.get('/api/children', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setChildren(childrenResponse.data);

        if (childrenResponse.data.length > 0) {
          const firstChildId = childrenResponse.data[0].id;
          const obsResponse = await api.get(`/api/observations/${firstChildId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          setObservations(obsResponse.data);
        }
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to load observation history.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    const refreshObservations = async () => {
      const token = localStorage.getItem(tokenKey);
      if (!token) return;

      if (children.length === 0) {
        setObservations([]);
        return;
      }

      try {
        if (selectedChildId === 'all') {
          let allObservations = [];
          for (const child of children) {
            const response = await api.get(`/api/observations/${child.id}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            allObservations = [...allObservations, ...response.data];
          }
          setObservations(allObservations);
          return;
        }

        const response = await api.get(`/api/observations/${selectedChildId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setObservations(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to fetch observations.');
      }
    };

    refreshObservations();
  }, [children, selectedChildId]);

  const filteredObservations = useMemo(() => {
    return observations.filter((observation) => {
      const matchesChild = selectedChildId === 'all' || String(observation.child_id) === String(selectedChildId);
      const matchesDomain = selectedDomain === 'all' || observation.domain === selectedDomain;
      const matchesDate = !selectedDate || new Date(observation.observation_date).toISOString().slice(0, 10) === selectedDate;
      return matchesChild && matchesDomain && matchesDate;
    });
  }, [observations, selectedChildId, selectedDomain, selectedDate]);

  const allDomains = ['Communication', 'Social Interaction', 'Play', 'Cognitive / Learning', 'Motor Skills', 'Adaptive / Daily Living', 'Emotional / Behavioral', 'General Development'];

  if (loading) {
    return <div className="page-shell"><div className="loading-card">Loading observation history...</div></div>;
  }

  return (
    <div className="page-shell dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">DevCare</div>
        <nav className="sidebar-nav">
          <Link to="/parent/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/parent/children" className="nav-item">Children</Link>
          <Link to="/parent/observations" className="nav-item">Observations</Link>
          <button className="nav-item active">History</button>
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Observation History</p>
            <h1>Review Observations</h1>
          </div>
          <Link to="/parent/dashboard" className="secondary-btn">Back to Dashboard</Link>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className="stat-card form-card">
          <div className="split-row history-filters">
            <label>
              Child
              <select value={selectedChildId} onChange={(event) => setSelectedChildId(event.target.value)}>
                <option value="all">All children</option>
                {children.map((child) => (
                  <option key={child.id} value={child.id}>{child.name}</option>
                ))}
              </select>
            </label>

            <label>
              Domain
              <select value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)}>
                <option value="all">All domains</option>
                {allDomains.map((domain) => (
                  <option key={domain} value={domain}>{domain}</option>
                ))}
              </select>
            </label>

            <label>
              Date
              <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
            </label>
          </div>

          <div className="button-row">
            <button
              type="button"
              className="secondary-btn"
              onClick={() => {
                setSelectedChildId('all');
                setSelectedDomain('all');
                setSelectedDate('');
              }}
            >
              Clear filters
            </button>
          </div>
        </section>

        <section className="stat-card list-card history-list">
          <h3>Observation Records</h3>
          {filteredObservations.length === 0 ? (
            <div>
              <p className="muted-text">No observations match the current filters.</p>
              <p className="muted-text">Tip: choose “All domains” and clear the date to see all saved observation records.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Domain</th>
                  <th>Skill</th>
                  <th>Observation</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredObservations.map((observation) => (
                  <tr key={observation.id}>
                    <td>{new Date(observation.observation_date).toLocaleDateString()}</td>
                    <td>{observation.domain}</td>
                    <td>{observation.skill}</td>
                    <td>{observation.observation_text}</td>
                    <td>{observation.confidence_score}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}

export default HistoryPage;
