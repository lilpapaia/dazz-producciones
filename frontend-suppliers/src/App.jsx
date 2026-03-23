import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import EditData from './pages/EditData';
import ChangeIban from './pages/ChangeIban';
import RequestDeactivation from './pages/RequestDeactivation';

function App() {
  return (
    <AuthProvider>
      <Router>
        <ErrorBoundary>
        <div className="min-h-screen bg-[#09090b] text-zinc-100">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<ProtectedRoute><Layout><Home /></Layout></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><Layout><Upload /></Layout></ProtectedRoute>} />
            <Route path="/notifications" element={<ProtectedRoute><Layout><Notifications /></Layout></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>} />
            <Route path="/profile/edit-data" element={<ProtectedRoute><Layout><EditData /></Layout></ProtectedRoute>} />
            <Route path="/profile/change-iban" element={<ProtectedRoute><Layout><ChangeIban /></Layout></ProtectedRoute>} />
            <Route path="/profile/deactivation" element={<ProtectedRoute><Layout><RequestDeactivation /></Layout></ProtectedRoute>} />
            <Route path="*" element={
              <div className="min-h-screen bg-[#09090b] flex items-center justify-center flex-col gap-3">
                <span className="font-['Bebas_Neue'] text-5xl text-zinc-800">404</span>
                <a href="/" className="text-amber-500 text-xs">Go home</a>
              </div>
            } />
          </Routes>
        </div>
        </ErrorBoundary>
      </Router>
    </AuthProvider>
  );
}

export default App;
