import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import SetPassword from './pages/SetPassword';
import Dashboard from './pages/Dashboard';
import ProjectCreate from './pages/ProjectCreate';
import ProjectView from './pages/ProjectView';
import ProjectCloseReview from './pages/ProjectCloseReview';
import UploadTickets from './pages/UploadTickets';
import ReviewTicket from './pages/ReviewTicket';
import Statistics from './pages/Statistics';
import Users from './pages/Users';

// PWA Components
import { PWAUpdatePrompt, PWAInstallPrompt } from './components/PWAComponents';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-zinc-950">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/set-password" element={<SetPassword />} />
            
            {/* Protected Routes con Navbar */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* NUEVA RUTA: Estadísticas */}
            <Route 
              path="/statistics" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <Statistics />
                </ProtectedRoute>
              } 
            />
            
            {/* Projects - ORDEN CORRECTO: específicas primero */}
            <Route 
              path="/projects/create" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <ProjectCreate />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/projects/:id/upload" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <UploadTickets />
                </ProtectedRoute>
              } 
            />
            
            {/* Preview antes de cerrar proyecto */}
            <Route 
              path="/projects/:id/close-review" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <ProjectCloseReview />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/projects/:id" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <ProjectView />
                </ProtectedRoute>
              } 
            />
            
            {/* Tickets */}
            <Route 
              path="/tickets/:id/review" 
              element={
                <ProtectedRoute>
                  <Navbar />
                  <ReviewTicket />
                </ProtectedRoute>
              } 
            />
            
            {/* Users - Admin only */}
            <Route 
              path="/users" 
              element={
                <ProtectedRoute adminOnly>
                  <Navbar />
                  <Users />
                </ProtectedRoute>
              } 
            />
          </Routes>
          
          {/* PWA Components - Toasts de actualización e instalación */}
          <PWAUpdatePrompt />
          <PWAInstallPrompt />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
