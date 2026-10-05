import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { tokenKey, roleKey, userIdKey } from '../auth';

function LoginPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError('');

    // Clean input data
    const payload = {
      email: formData.email.trim().toLowerCase(),
      password: formData.password,
    };

    try {
      // Send cleaned payload to backend API
      const response = await api.post('/api/auth/login', payload);

      // Display backend response for debugging
      console.log('Login response:', response.data);

      const accessToken = response.data.access_token;
      const backendRole = response.data.role;
      const userId = response.data.user_id;

      // Validate access token
      if (!accessToken) {
        setError('Login failed: Access token is missing.');
        return;
      }

      // Normalize role
      const role = String(backendRole || '')
        .toLowerCase()
        .trim();

      // Validate role
      if (!role) {
        setError('Login failed: User role is missing.');
        console.error('Role missing in backend response:', response.data);
        return;
      }

      // Save login details in localStorage
      localStorage.setItem(tokenKey, accessToken);
      localStorage.setItem(roleKey, role);
      localStorage.setItem(userIdKey, String(userId || ''));

      // Verify saved values
      console.log('Saved token:', localStorage.getItem(tokenKey));
      console.log('Saved role:', localStorage.getItem(roleKey));
      console.log('Saved user ID:', localStorage.getItem(userIdKey));

      // Redirect based on role
      if (role === 'parent') {
        navigate('/parent/dashboard', { replace: true });
      } else if (role === 'professional') {
        navigate('/professional/dashboard', { replace: true });
      } else if (role === 'admin') {
        navigate('/admin/dashboard', { replace: true });
      } else {
        // Remove invalid login details
        localStorage.removeItem(tokenKey);
        localStorage.removeItem(roleKey);
        localStorage.removeItem(userIdKey);

        setError(`Unknown user role: ${role}`);
        console.error('Unknown role received from backend:', role);
      }
    } catch (requestError) {
      console.error('Login error:', requestError);

      if (!requestError.response) {
        setError(
          'Backend unavailable. Please make sure the API server is running.'
        );
        return;
      }

      const statusCode = requestError.response.status;
      const detail = requestError.response.data?.detail;

      if (statusCode === 401) {
        setError('Invalid email or password.');
      } else if (statusCode === 422) {
        // FastAPI 422 returns an array of error objects. Extract the message:
        if (Array.isArray(detail) && detail.length > 0) {
          setError(detail[0].msg || 'Validation error. Please check your inputs.');
        } else {
          setError('Validation error. Please check your inputs.');
        }
      } else {
        // Safely extract string message or fallback
        setError(
          typeof detail === 'string'
            ? detail
            : 'Unable to log in right now.'
        );
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
          <h2>Welcome back</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
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
            Password
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </label>

          {error && <div className="error-box">{error}</div>}

          <button
            type="submit"
            className="primary-btn"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Login'}
          </button>
        </form>

        <p className="switch-text">
          Need an account? <Link to="/register">Register here</Link>
        </p>

        <p className="switch-text">
          <Link to="/">Back to home</Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;