import { Link, useLocation } from 'react-router-dom';
import { Home, FileText, Upload, User } from 'lucide-react';

const tabs = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/invoices', icon: FileText, label: 'Invoices' },
  { path: '/upload', icon: Upload, label: 'Upload' },
  { path: '/profile', icon: User, label: 'Profile' },
];

const BottomNav = () => {
  const { pathname } = useLocation();

  return (
    <nav className="fixed bottom-0 inset-x-0 bg-zinc-900 border-t border-zinc-800 z-50 flex safe-bottom">
      {tabs.map(t => {
        const active = pathname === t.path;
        return (
          <Link
            key={t.path}
            to={t.path}
            className={`flex-1 flex flex-col items-center gap-0.5 py-2.5 transition-colors ${active ? 'text-amber-500' : 'text-zinc-600'}`}
          >
            <t.icon size={18} />
            <span className="text-[9px] tracking-wider uppercase">{t.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};

export default BottomNav;
