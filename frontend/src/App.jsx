import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';
import ProjectCreate from './pages/ProjectCreate';
import UploadTickets from './pages/UploadTickets';
import ReviewTicket from './pages/ReviewTicket';
import Users from './pages/Users';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <>
                  <Navbar />
                  <Dashboard />
                </>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/new"
            element={
              <ProtectedRoute>
                <>
                  <Navbar />
                  <ProjectCreate />
                </>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <>
                  <Navbar />
                  <ProjectView />
                </>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:id/upload"
            element={
              <ProtectedRoute>
                <>
                  <Navbar />
                  <UploadTickets />
                </>
              </ProtectedRoute>
            }
          />

          <Route
            path="/tickets/:id/review"
            element={
              <ProtectedRoute>
                <>
                  <Navbar />
                  <ReviewTicket />
                </>
              </ProtectedRoute>
            }
          />

          <Route
            path="/users"
            element={
              <ProtectedRoute adminOnly>
                <>
                  <Navbar />
                  <Users />
                </>
              </ProtectedRoute>
            }
          />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
