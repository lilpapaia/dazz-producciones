import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, FolderOpen, Users, LogOut } from 'lucide-react';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            {/* Logo SVG de Dazz Creative */}
            <svg xmlns="http://www.w3.org/2000/svg" width="140" height="14" viewBox="0 0 708 69" fill="none" className="text-amber-500">
              <path d="M58.7442 59.5633L46.4651 68.332L32.7907 50.377L19.5349 68.332L6.97674 59.5633L20.3721 40.634L0 34.2314L4.60465 20.1736L24.5581 26.5761V3.33203H41.0233V26.5761L60.9767 20.1736L66 34.2314L45.3488 40.634L58.7442 59.5633Z" fill="currentColor"/>
              <path d="M117.987 55.1217H129.049C140.689 55.1217 145.691 47.8108 145.691 33.3812C145.691 18.9517 140.689 13.1798 127.895 13.1798H117.987V55.1217ZM131.743 65.992H105V2.11719H129.723C147.038 2.11719 159.351 13.9494 159.351 33.3812C159.351 52.813 148.289 65.992 131.743 65.992Z" fill="currentColor"/>
              <path d="M192.939 41.8466L184.955 16.4505H184.859L176.682 41.8466H192.939ZM215.353 65.992H200.827L196.787 52.813H173.219L168.698 65.992H154.557L177.355 2.11719H192.843L215.353 65.992Z" fill="currentColor"/>
              <path d="M266.393 65.992H216.467V54.6408L249.655 13.276H217.429V2.11719H266.393V12.6027L233.013 54.6408H266.393V65.992Z" fill="currentColor"/>
              <path d="M319.283 65.992H269.356V54.6408L302.544 13.276H270.318V2.11719H319.283V12.6027L285.902 54.6408H319.283V65.992Z" fill="currentColor"/>
            </svg>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard"
              className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                isActive('/dashboard')
                  ? 'bg-amber-500 text-zinc-950'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
              }`}
            >
              <LayoutDashboard size={18} />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>

            <Link
              to="/projects"
              className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                location.pathname.startsWith('/projects')
                  ? 'bg-amber-500 text-zinc-950'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
              }`}
            >
              <FolderOpen size={18} />
              <span className="hidden sm:inline">Proyectos</span>
            </Link>

            {user.role === 'admin' && (
              <Link
                to="/users"
                className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                  isActive('/users')
                    ? 'bg-amber-500 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                <Users size={18} />
                <span className="hidden sm:inline">Usuarios</span>
              </Link>
            )}

            {/* User Info & Logout */}
            <div className="flex items-center gap-3 ml-4 pl-4 border-l border-zinc-800">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-zinc-100">{user.name}</p>
                <p className="text-xs text-zinc-500">{user.role}</p>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 text-zinc-400 hover:text-red-400 hover:bg-zinc-800 rounded-sm transition-colors"
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
