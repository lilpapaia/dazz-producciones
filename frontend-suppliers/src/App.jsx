import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import BottomNav from './components/BottomNav';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Profile from './pages/Profile';

const PortalShell = ({ children }) => (
  <>
    <Navbar />
    <main className="pb-[80px]">{children}</main>
    <BottomNav />
  </>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-[#09090b] text-zinc-100">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<ProtectedRoute><PortalShell><Home /></PortalShell></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><PortalShell><Upload /></PortalShell></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><PortalShell><Profile /></PortalShell></ProtectedRoute>} />
            <Route path="*" element={
              <div className="min-h-screen bg-[#09090b] flex items-center justify-center flex-col gap-3">
                <span className="font-['Bebas_Neue'] text-5xl text-zinc-800">404</span>
                <a href="/" className="text-amber-500 text-xs">Go home</a>
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
