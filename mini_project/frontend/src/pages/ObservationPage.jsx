import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { tokenKey } from '../auth';

const ruleBasedClassifier = (text) => {
  const normalized = text.toLowerCase();

  if (/(talk|speak|word|language|say|communicate)/.test(normalized)) {
    return {
      domain: 'Communication',
      skill: 'Expressive communication',
      behavior: 'Uses words or spoken communication',
      confidence: 85,
    };
  }

  if (/(turn|share|friend|social|smile|play with|join)/.test(normalized)) {
    return {
      domain: 'Social Interaction',
      skill: 'Social engagement',
      behavior: 'Participates in reciprocal social interaction',
      confidence: 80,
    };
  }

  if (/(play|toy|game|ball|blocks|pretend)/.test(normalized)) {
    return {
      domain: 'Play',
      skill: 'Play participation',
      behavior: 'Engages in play and exploratory interaction',
      confidence: 82,
    };
  }

  if (/(walk|run|jump|climb|kick|throw|catch)/.test(normalized)) {
    return {
      domain: 'Motor Skills',
      skill: 'Gross motor movement',
      behavior: 'Uses movement and motor action',
      confidence: 87,
    };
  }

  return {
    domain: 'General Development',
    skill: 'General observation',
    behavior: 'Emerging developmental engagement',
    confidence: 60,
  };
};

function ObservationPage() {
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [observationText, setObservationText] = useState('');
  const [observationDate, setObservationDate] = useState(new Date().toISOString().slice(0, 10));
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);

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
        setError(requestError.response?.data?.detail || 'Unable to load children.');
      } finally {
        setLoading(false);
      }
    };

    fetchChildren();
  }, []);

  const handleAnalyze = () => {
    if (!selectedChildId || !observationText.trim()) {
      setError('Please select a child and provide observation text.');
      return;
    }

    const result = ruleBasedClassifier(observationText);
    setAnalysis({
      ...result,
      observation_text: observationText,
      observation_date: observationDate,
    });
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    if (!analysis) return;

    const token = localStorage.getItem(tokenKey);
    try {
      await api.post(
        '/api/observations',
        {
          child_id: Number(selectedChildId),
          observation_text: analysis.observation_text,
          domain: analysis.domain,
          skill: analysis.skill,
          behavior: analysis.behavior,
          confidence_score: analysis.confidence,
          observation_date: new Date(`${analysis.observation_date}T12:00:00`).toISOString(),
        },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setSuccess('Observation saved successfully.');
      setAnalysis(null);
      setObservationText('');
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to save observation.');
    }
  };

  const childOptions = useMemo(() => children, [children]);

  if (loading) {
    return <div className="page-shell"><div className="loading-card">Loading observations...</div></div>;
  }

  return (
    <div className="page-shell dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">DevCare</div>
        <nav className="sidebar-nav">
          <Link to="/parent/dashboard" className="nav-item">Dashboard</Link>
          <Link to="/parent/children" className="nav-item">Children</Link>
          <button className="nav-item active">Observations</button>
          <Link to="/parent/history" className="nav-item">History</Link>
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Prototype Observation Analysis</p>
            <h1>Developmental Observations</h1>
          </div>
          <Link to="/parent/dashboard" className="secondary-btn">Back to Dashboard</Link>
        </header>

        {error && <div className="error-box">{error}</div>}
        {success && <div className="success-box">{success}</div>}

        <section className="stats-grid two-cols">
          <div className="stat-card form-card">
            <h3>New Observation</h3>
            <form className="auth-form compact-form" onSubmit={(event) => event.preventDefault()}>
              <label>
                Select Child
                <select value={selectedChildId} onChange={(event) => setSelectedChildId(event.target.value)}>
                  <option value="">Select a child</option>
                  {childOptions.map((child) => (
                    <option key={child.id} value={child.id}>{child.name}</option>
                  ))}
                </select>
              </label>

              <label>
                Observation Date
                <input type="date" value={observationDate} onChange={(event) => setObservationDate(event.target.value)} />
              </label>

              <label>
                Observation Text
                <textarea
                  value={observationText}
                  onChange={(event) => setObservationText(event.target.value)}
                  rows="6"
                  placeholder="My child played with me for 10 minutes and took turns rolling the ball."
                />
              </label>

              <button type="button" className="primary-btn" onClick={handleAnalyze}>Analyze Observation</button>
            </form>
          </div>

          <div className="stat-card form-card">
            <h3>Review Before Save</h3>
            {analysis ? (
              <div className="analysis-box">
                <p><strong>Detected Domain:</strong> {analysis.domain}</p>
                <p><strong>Detected Skill:</strong> {analysis.skill}</p>
                <p><strong>Detected Behavior:</strong> {analysis.behavior}</p>
                <p><strong>Confidence:</strong> {analysis.confidence}%</p>
                <div className="button-row">
                  <button type="button" className="primary-btn" onClick={handleSave}>Save Observation</button>
                  <button type="button" className="secondary-btn" onClick={() => setAnalysis(null)}>Edit Analysis</button>
                </div>
              </div>
            ) : (
              <p className="muted-text">No analysis yet. Add observation details and run the prototype classifier.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default ObservationPage;
