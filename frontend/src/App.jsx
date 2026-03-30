import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';

// Eager load: Login (primera pantalla) + Dashboard (destino principal)
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Lazy load: páginas secundarias (cargan bajo demanda)
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const SetPassword = lazy(() => import('./pages/SetPassword'));
const ProjectCreate = lazy(() => import('./pages/ProjectCreate'));
const ProjectView = lazy(() => import('./pages/ProjectView'));
const ProjectCloseReview = lazy(() => import('./pages/ProjectCloseReview'));
const UploadTickets = lazy(() => import('./pages/UploadTickets'));
const ReviewTicket = lazy(() => import('./pages/ReviewTicket'));
const Statistics = lazy(() => import('./pages/Statistics'));
const Users = lazy(() => import('./pages/Users'));

// Suppliers module (admin only)
const SuppliersLayout = lazy(() => import('./pages/suppliers/SuppliersLayout'));
const SuppliersDashboard = lazy(() => import('./pages/suppliers/SuppliersDashboard'));
const SuppliersList = lazy(() => import('./pages/suppliers/SuppliersList'));
const SupplierDetail = lazy(() => import('./pages/suppliers/SupplierDetail'));
const InvoicesList = lazy(() => import('./pages/suppliers/InvoicesList'));
const SupplierInvite = lazy(() => import('./pages/suppliers/SupplierInvite'));
const SupplierNotifications = lazy(() => import('./pages/suppliers/SupplierNotifications'));
const InvoiceDetail = lazy(() => import('./pages/suppliers/InvoiceDetail'));
const AutoInvoice = lazy(() => import('./pages/suppliers/AutoInvoice'));

// PWA Components
import { PWAUpdatePrompt, PWAInstallPrompt } from './components/PWAComponents';

// F-001: 404 catch-all
const NotFound = () => (
  <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-center p-4">
    <div>
      <p className="text-6xl font-bebas text-amber-500 mb-4">404</p>
      <p className="text-zinc-400 mb-6">Página no encontrada</p>
      <a href="/dashboard" className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all">
        IR AL DASHBOARD
      </a>
    </div>
  </div>
);

// Loading fallback branded
const PageLoader = () => (
  <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-zinc-500 text-sm tracking-wider uppercase font-mono">Cargando...</span>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <ErrorBoundary>
        <div className="min-h-screen bg-zinc-950">
          <Suspense fallback={<PageLoader />}>
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
            
            {/* NUEVA RUTA: Estadísticas - Solo ADMIN y BOSS */}
            <Route 
              path="/statistics" 
              element={
                <ProtectedRoute adminOrBossOnly>
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

            {/* Suppliers module - Admin only */}
            <Route
              path="/suppliers"
              element={
                <ProtectedRoute adminOnly>
                  <Navbar />
                  <SuppliersLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<SuppliersDashboard />} />
              <Route path="list" element={<SuppliersList />} />
              <Route path="invoices" element={<InvoicesList />} />
              <Route path="invoices/:invoiceId" element={<InvoiceDetail />} />
              <Route path="invite" element={<SupplierInvite />} />
              <Route path="autoinvoice" element={<AutoInvoice />} />
              <Route path="notifications" element={<SupplierNotifications />} />
              <Route path=":id" element={<SupplierDetail />} />
            </Route>
            {/* 404 catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          </Suspense>

          {/* UX-H1: Toast notifications (reemplaza alert() nativo) */}
          <Toaster
            position="top-center"
            toastOptions={{
              style: { background: '#27272a', color: '#f4f4f5', border: '1px solid #3f3f46' },
              className: 'text-sm',
            }}
          />

          {/* PWA Components - Toasts de actualización e instalación */}
          <PWAUpdatePrompt />
          <PWAInstallPrompt />
        </div>
        </ErrorBoundary>
      </Router>
    </AuthProvider>
  );
}

export default App;
