import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { tokenKey } from '../auth';

const emptyForm = {
  name: '',
  date_of_birth: '',
  age: '',
  gender: '',
  interests: '',
  communication_preferences: '',
  notes: '',
};

function ChildProfilePage() {
  const navigate = useNavigate();
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [formData, setFormData] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(tokenKey);
    if (!token) {
      navigate('/login');
      return;
    }

    fetchChildren(token);
  }, [navigate]);

  const fetchChildren = async (token) => {
    try {
      const response = await api.get('/api/children', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChildren(response.data);
      if (response.data.length > 0 && !selectedChildId) {
        setSelectedChildId(String(response.data[0].id));
      }
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to load children.');
    } finally {
      setLoading(false);
    }
  };

  const selectedChild = useMemo(
    () => children.find((child) => String(child.id) === String(selectedChildId)) || null,
    [children, selectedChildId],
  );

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setFormData(emptyForm);
    setEditingId(null);
    setSuccess('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const token = localStorage.getItem(tokenKey);

    try {
      const payload = {
        ...formData,
        age: formData.age === '' ? null : Number(formData.age),
      };

      if (editingId) {
        await api.put(`/api/children/${editingId}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSuccess('Child profile updated successfully.');
      } else {
        await api.post('/api/children', payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSuccess('Child profile created successfully.');
      }

      const response = await api.get('/api/children', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChildren(response.data);
      setSelectedChildId(String(response.data[0]?.id || ''));
      resetForm();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to save the child profile.');
    }
  };

  const editChild = (child) => {
    setEditingId(child.id);
    setSelectedChildId(String(child.id));
    setFormData({
      name: child.name || '',
      date_of_birth: child.date_of_birth || '',
      age: child.age ?? '',
      gender: child.gender || '',
      interests: child.interests || '',
      communication_preferences: child.communication_preferences || '',
      notes: child.notes || '',
    });
    setError('');
    setSuccess('');
  };

  const deleteChild = async (childId) => {
    const confirmed = window.confirm('Delete this child profile? This action cannot be undone.');
    if (!confirmed) return;

    const token = localStorage.getItem(tokenKey);
    try {
      await api.delete(`/api/children/${childId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const response = await api.get('/api/children', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChildren(response.data);
      setSelectedChildId(String(response.data[0]?.id || ''));
      if (editingId === childId) {
        resetForm();
      }
      setSuccess('Child profile deleted successfully.');
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to delete child profile.');
    }
  };

  if (loading) {
    return <div className="page-shell"><div className="loading-card">Loading child profiles...</div></div>;
  }

  return (
    <div className="page-shell dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">DevCare</div>
        <nav className="sidebar-nav">
          <Link to="/parent/dashboard" className="nav-item">Dashboard</Link>
          <button className="nav-item active">Children</button>
          <Link to="/parent/observations" className="nav-item">Observations</Link>
          <Link to="/parent/history" className="nav-item">History</Link>
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Child Profile Management</p>
            <h1>Children</h1>
          </div>
          <Link to="/parent/dashboard" className="secondary-btn">Back to Dashboard</Link>
        </header>

        {error && <div className="error-box">{error}</div>}
        {success && <div className="success-box">{success}</div>}

        <section className="stats-grid two-cols">
          <div className="stat-card form-card">
            <h3>{editingId ? 'Edit Child Profile' : 'Create Child Profile'}</h3>
            <form onSubmit={handleSubmit} className="auth-form compact-form">
              <label>
                Child Name
                <input type="text" name="name" value={formData.name} onChange={handleChange} required />
              </label>

              <div className="split-row">
                <label>
                  Date of Birth
                  <input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} />
                </label>
                <label>
                  Age
                  <input type="number" name="age" min="0" max="25" value={formData.age} onChange={handleChange} />
                </label>
              </div>

              <label>
                Gender
                <input type="text" name="gender" value={formData.gender} onChange={handleChange} placeholder="e.g. Female, Male, Other" />
              </label>

              <label>
                Interests
                <textarea name="interests" value={formData.interests} onChange={handleChange} rows="3" />
              </label>

              <label>
                Communication Preferences
                <textarea name="communication_preferences" value={formData.communication_preferences} onChange={handleChange} rows="3" />
              </label>

              <label>
                Notes
                <textarea name="notes" value={formData.notes} onChange={handleChange} rows="4" />
              </label>

              <div className="button-row">
                <button type="submit" className="primary-btn">{editingId ? 'Update Child' : 'Add Child'}</button>
                <button type="button" className="secondary-btn" onClick={resetForm}>Cancel</button>
              </div>
            </form>
          </div>

          <div className="stat-card list-card">
            <h3>Child Selector</h3>
            <label>
              Select Child
              <select value={selectedChildId} onChange={(event) => setSelectedChildId(event.target.value)}>
                <option value="">Select a child</option>
                {children.map((child) => (
                  <option key={child.id} value={child.id}>{child.name}</option>
                ))}
              </select>
            </label>

            {selectedChild ? (
              <div className="child-detail-box">
                <h4>{selectedChild.name}</h4>
                <p><strong>DOB:</strong> {selectedChild.date_of_birth || 'Not provided'}</p>
                <p><strong>Age:</strong> {selectedChild.age ?? 'Not provided'}</p>
                <p><strong>Gender:</strong> {selectedChild.gender || 'Not provided'}</p>
                <p><strong>Interests:</strong> {selectedChild.interests || 'Not provided'}</p>
                <p><strong>Communication:</strong> {selectedChild.communication_preferences || 'Not provided'}</p>
                <p><strong>Notes:</strong> {selectedChild.notes || 'Not provided'}</p>
                <div className="button-row">
                  <button type="button" className="secondary-btn" onClick={() => editChild(selectedChild)}>Edit</button>
                  <button type="button" className="secondary-btn danger" onClick={() => deleteChild(selectedChild.id)}>Delete</button>
                </div>
              </div>
            ) : (
              <p className="muted-text">No child selected.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default ChildProfilePage;
