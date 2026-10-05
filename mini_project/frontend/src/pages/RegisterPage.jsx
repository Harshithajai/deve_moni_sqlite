import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// 1. Define the API base URL
const API_URL = import.meta.env.VITE_API_BASE_URL || "https://deve-moni-backend.onrender.com";

// 2. Register function using proper endpoint path (/api/auth/register)
const handleRegister = async (userData) => {
  try {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Registration failed");
    }

    return data;
  } catch (error) {
    console.error("Error registering user:", error);
    throw error;
  }
};

function RegisterPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    role: 'parent',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match.');
      setLoading(false);
      return;
    }

    try {
      await handleRegister(formData);
      setSuccess('Registration successful. Redirecting to login...');
      setTimeout(() => navigate('/login'), 1200);
    } catch (requestError) {
      const backendMessage = requestError.message || 'Registration failed.';
      if (backendMessage === 'Failed to fetch') {
        setError('Backend unavailable. Please make sure the API server is running and accessible.');
      } else {
        setError(backendMessage);
      }
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <div className="brand-mark small">D</div>
          <h2>Create your account</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Full Name
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Your full name"
              required
            />
          </label>

          <label>
            Email
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
            />
          </label>

          <label>
            Account Type
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
            >
              <option value="parent">Parent / Caregiver</option>
              <option value="professional">Professional (Therapist, Teacher, etc.)</option>
            </select>
          </label>

          <label>
            Password
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="At least 8 characters"
              required
            />
          </label>

          <label>
            Confirm Password
            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="Confirm your password"
              required
            />
          </label>

          {error && <div className="error-box">{error}</div>}
          {success && <div className="success-box">{success}</div>}

          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="switch-text">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
        <p className="switch-text">
          <Link to="/">Back to home</Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
