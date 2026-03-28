import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';

// Eager: first screens
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';

// Lazy: secondary pages
const Upload = lazy(() => import('./pages/Upload'));
const Profile = lazy(() => import('./pages/Profile'));
const Notifications = lazy(() => import('./pages/Notifications'));
const EditData = lazy(() => import('./pages/EditData'));
const ChangeIban = lazy(() => import('./pages/ChangeIban'));
const RequestDeactivation = lazy(() => import('./pages/RequestDeactivation'));

const PageLoader = () => (
  <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
    <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <ErrorBoundary>
        <div className="min-h-screen bg-[#09090b] text-zinc-100">
          <Suspense fallback={<PageLoader />}>
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
          </Suspense>
        </div>
        </ErrorBoundary>
      </Router>
    </AuthProvider>
  );
}

export default App;
