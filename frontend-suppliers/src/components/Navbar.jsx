import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

const Navbar = () => {
  const { supplier, logout } = useAuth();
  const navigate = useNavigate();
  const initials = supplier?.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??';

  const handleLogout = async () => { await logout(); navigate('/login'); };

  return (
    <header className="px-4 pt-3 pb-2 flex items-center justify-between">
      <div>
        <div className="text-[9px] text-amber-500 tracking-[.14em] font-['Bebas_Neue']">DAZZ GROUP</div>
        <div className="font-['Bebas_Neue'] text-[16px] tracking-wide text-zinc-100 leading-tight">Supplier Portal</div>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-amber-500/15 flex items-center justify-center text-[11px] font-bold text-amber-400 font-['Bebas_Neue']">
          {initials}
        </div>
        <button onClick={handleLogout} className="text-zinc-600 hover:text-red-400 transition-colors p-1" title="Logout">
          <LogOut size={15} strokeWidth={1.5} />
        </button>
      </div>
    </header>
  );
};

export default Navbar;
