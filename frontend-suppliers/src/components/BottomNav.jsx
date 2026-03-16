import { Link, useLocation } from 'react-router-dom';
import { Home, Upload, User } from 'lucide-react';

const tabs = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/upload', icon: Upload, label: 'Upload' },
  { path: '/profile', icon: User, label: 'My data' },
];

const BottomNav = () => {
  const { pathname } = useLocation();

  return (
    <nav className="fixed bottom-0 inset-x-0 bg-[#18181b] border-t border-zinc-800 z-50 flex items-center justify-around h-[72px] px-2 pb-[env(safe-area-inset-bottom)]">
      {tabs.map(t => {
        const active = pathname === t.path;
        return (
          <Link key={t.path} to={t.path} className="flex-1 flex flex-col items-center gap-[3px] py-1.5">
            <t.icon size={20} className={active ? 'text-amber-500' : 'text-zinc-600'} strokeWidth={1.5} />
            <span className={`text-[9px] tracking-wide ${active ? 'text-amber-400' : 'text-zinc-600'}`}>{t.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};

export default BottomNav;
