import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Users, LogOut, Truck, ExternalLink } from 'lucide-react';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-3 sm:px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo DAZZ CREATIVE - Solo asterisco en móvil */}
          <Link to="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            {/* Logo asterisco SVG */}
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 66 69" fill="none" className="text-amber-500 flex-shrink-0">
              <path d="M58.7442 59.5633L46.4651 68.332L32.7907 50.377L19.5349 68.332L6.97674 59.5633L20.3721 40.634L0 34.2314L4.60465 20.1736L24.5581 26.5761V3.33203H41.0233V26.5761L60.9767 20.1736L66 34.2314L45.3488 40.634L58.7442 59.5633Z" fill="currentColor"/>
            </svg>
            {/* Texto DAZZ CREATIVE - Oculto en móvil */}
            <span className="hidden sm:inline text-xl font-bold tracking-wider text-white uppercase">DAZZ CREATIVE</span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-1 sm:gap-2">
            <Link
              to="/dashboard"
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                isActive('/dashboard')
                  ? 'bg-amber-500 text-zinc-950'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
              }`}
            >
              <LayoutDashboard size={18} />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>

            {/* Estadísticas — solo ADMIN y BOSS */}
            {(user.role === 'ADMIN' || user.role === 'BOSS') && (
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
            {user.role === 'ADMIN' && (
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
            {user.role === 'ADMIN' && (
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

            {/* Portal proveedores — solo ADMIN */}
            {user.role === 'ADMIN' && (
              <a
                href="https://providers.dazzcreative.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-sm text-xs font-medium text-zinc-500 hover:text-amber-400 border border-zinc-800 hover:border-amber-500/50 transition-colors"
                title="Supplier Portal"
              >
                <ExternalLink size={14} />
                <span className="hidden sm:inline">Portal</span>
              </a>
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
