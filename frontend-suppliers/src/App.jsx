import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import BottomNav from './components/BottomNav';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Invoices from './pages/Invoices';
import Upload from './pages/Upload';
import Profile from './pages/Profile';

const PortalLayout = ({ children }) => (
  <>
    <Navbar />
    <main className="pb-20 min-h-[calc(100vh-56px)]">{children}</main>
    <BottomNav />
  </>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-zinc-950">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<ProtectedRoute><PortalLayout><Dashboard /></PortalLayout></ProtectedRoute>} />
            <Route path="/invoices" element={<ProtectedRoute><PortalLayout><Invoices /></PortalLayout></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><PortalLayout><Upload /></PortalLayout></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><PortalLayout><Profile /></PortalLayout></ProtectedRoute>} />
            <Route path="*" element={
              <div className="min-h-screen bg-zinc-950 flex items-center justify-center flex-col gap-3">
                <span className="font-['Bebas_Neue'] text-4xl text-zinc-700">404</span>
                <a href="/" className="text-amber-500 text-sm hover:text-amber-400">Go home</a>
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
