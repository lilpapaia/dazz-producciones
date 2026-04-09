import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Users, LogOut, Truck } from 'lucide-react';
import DazzLogo from './DazzLogo';
import { ROLES } from '../constants/roles';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-3 sm:px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo DAZZ CREATIVE - Solo asterisco en móvil */}
          <Link to="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <DazzLogo size={32} className="text-amber-500 flex-shrink-0" />
            {/* Texto DAZZ CREATIVE - Oculto en móvil */}
            <span className="hidden sm:inline text-xl font-bold tracking-wider text-white uppercase">DAZZ CREATIVE</span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-1 sm:gap-2">
            <Link
              to="/dashboard"
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                (isActive('/dashboard') || location.pathname === '/')
                  ? 'bg-amber-500 text-zinc-950'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
              }`}
            >
              <LayoutDashboard size={18} />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>

            {/* Estadísticas — solo ADMIN y BOSS */}
            {(user.role === ROLES.ADMIN || user.role === ROLES.BOSS) && (
              <Link
                to="/statistics"
                className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                  isActive('/statistics')
                    ? 'bg-amber-500 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                <BarChart3 size={18} />
                <span className="hidden sm:inline">Estadísticas</span>
              </Link>
            )}

            {/* Proveedores — solo ADMIN */}
            {user.role === ROLES.ADMIN && (
              <Link
                to="/suppliers"
                className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                  isActive('/suppliers')
                    ? 'bg-amber-500 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                <Truck size={18} />
                <span className="hidden sm:inline">Proveedores</span>
              </Link>
            )}

            {/* Usuarios — solo ADMIN */}
            {user.role === ROLES.ADMIN && (
              <Link
                to="/users"
                className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                  isActive('/users')
                    ? 'bg-amber-500 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                <Users size={18} />
                <span className="hidden sm:inline">Usuarios</span>
              </Link>
            )}

            {/* User Info & Logout - Más separado en móvil */}
            <div className="flex items-center gap-2 sm:gap-3 ml-2 sm:ml-4 pl-2 sm:pl-4 border-l border-zinc-800">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-zinc-100">{user.name}</p>
                <p className="text-xs text-zinc-500">{user.role}</p>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-2 sm:px-3 py-2 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded-sm transition-colors"
                title="Cerrar sesión"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
