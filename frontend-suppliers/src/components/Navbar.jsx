import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

const Navbar = () => {
  const { supplier, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const initials = supplier?.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??';

  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50 px-4 h-14 flex items-center justify-between">
      <span className="font-['Bebas_Neue'] text-lg tracking-wider text-amber-500">DAZZ GROUP</span>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center text-[11px] font-bold text-zinc-950">{initials}</div>
        <span className="text-xs text-zinc-400 hidden sm:block">{supplier?.name}</span>
        <button onClick={handleLogout} className="text-zinc-500 hover:text-red-400 transition-colors p-1" title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
