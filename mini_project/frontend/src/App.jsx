import { Navigate, Route, Routes } from 'react-router-dom';

import { isAuthenticated, getRole } from './auth';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

import DashboardPage from './pages/DashboardPage';
import ChildProfilePage from './pages/ChildProfilePage';
import ObservationPage from './pages/ObservationPage';
import HistoryPage from './pages/HistoryPage';
import ProgressPage from './pages/ProgressPage';

import ProfessionalDashboardPage from './pages/ProfessionalDashboardPage';
import ConnectProfessionalPage from './pages/ConnectProfessionalPage';

import Assistant from './components/Assistant';


function ProtectedRoute({ children, requiredRole = null }) {

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {

    const userRole = getRole();

    if (userRole !== requiredRole) {

      if (userRole === 'parent') {
        return <Navigate to="/parent/dashboard" replace />;
      }

      if (userRole === 'professional') {
        return <Navigate to="/professional/dashboard" replace />;
      }

      if (userRole === 'admin') {
        return <Navigate to="/admin/dashboard" replace />;
      }

      return <Navigate to="/login" replace />;
    }
  }

  return children;
}


function App() {

  return (

    <Routes>

      {/* Public Routes */}

      <Route
        path="/"
        element={<LandingPage />}
      />

      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/register"
        element={<RegisterPage />}
      />


      {/* Parent/Caregiver Routes */}

      <Route
        path="/parent/dashboard"
        element={
          <ProtectedRoute requiredRole="parent">
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/parent/children"
        element={
          <ProtectedRoute requiredRole="parent">
            <ChildProfilePage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/parent/observations"
        element={
          <ProtectedRoute requiredRole="parent">
            <ObservationPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/parent/history"
        element={
          <ProtectedRoute requiredRole="parent">
            <HistoryPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/parent/progress"
        element={
          <ProtectedRoute requiredRole="parent">
            <ProgressPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/parent/assistant"
        element={
          <ProtectedRoute requiredRole="parent">
            <Assistant />
          </ProtectedRoute>
        }
      />


      {/* Parent - Connect Professional */}

      <Route
        path="/parent/connect-professional"
        element={
          <ProtectedRoute requiredRole="parent">
            <ConnectProfessionalPage />
          </ProtectedRoute>
        }
      />


      {/* Professional Routes */}

      <Route
        path="/professional/dashboard"
        element={
          <ProtectedRoute requiredRole="professional">
            <ProfessionalDashboardPage />
          </ProtectedRoute>
        }
      />


      {/* Admin Routes */}

      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute requiredRole="admin">

            <div
              style={{
                padding: '2rem',
                textAlign: 'center'
              }}
            >

              <h1>Admin Dashboard</h1>

              <p>
                Coming Soon: Manage users, view system statistics,
                and manage documents.
              </p>

            </div>

          </ProtectedRoute>
        }
      />


      {/* Backward Compatibility */}

      <Route
        path="/dashboard"
        element={
          <Navigate
            to="/parent/dashboard"
            replace
          />
        }
      />

      <Route
        path="/children"
        element={
          <Navigate
            to="/parent/children"
            replace
          />
        }
      />

      <Route
        path="/observations"
        element={
          <Navigate
            to="/parent/observations"
            replace
          />
        }
      />

      <Route
        path="/history"
        element={
          <Navigate
            to="/parent/history"
            replace
          />
        }
      />

      <Route
        path="/progress"
        element={
          <Navigate
            to="/parent/progress"
            replace
          />
        }
      />


      {/* Unknown Routes */}

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />

    </Routes>

  );

}


export default App;