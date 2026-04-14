import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Upload, Bell, User, LogOut, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { getSummary, getPendingDocuments } from '../services/api';
import DazzLogo from './DazzLogo';

const NAV_ITEMS = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/upload', icon: Upload, label: 'Upload invoice' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/notifications', icon: Bell, label: 'Notifications' },
  { path: '/profile', icon: User, label: 'My profile' },
];

const Layout = ({ children }) => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { supplier, logout } = useAuth();
  const [unread, setUnread] = useState(0);
  const [pendingDocs, setPendingDocs] = useState(0);
  const initials = supplier?.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??';

  useEffect(() => {
    const doFetch = () => getSummary().then(r => setUnread(r.data.unread_notifications || 0)).catch(() => {});
    doFetch();
    if (pathname !== '/') return;
    let interval = setInterval(doFetch, 30000);
    const handleVisibility = () => {
      clearInterval(interval);
      if (document.visibilityState === 'visible') {
        doFetch();
        interval = setInterval(doFetch, 30000);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => { clearInterval(interval); document.removeEventListener('visibilitychange', handleVisibility); };
  }, [pathname]);

  // FEAT-06: Fetch pending legal documents count
  useEffect(() => {
    getPendingDocuments().then(r => setPendingDocs(r.data?.length || 0)).catch(() => {});
  }, [pathname]);

  const handleLogout = async () => { await logout(); navigate('/login'); };

  const isActive = (path) => {
    if (path === '/') return pathname === '/';
    return pathname.startsWith(path);
  };

  return (
    <div className="flex min-h-screen">
      {/* ═══ SIDEBAR — desktop only ═══ */}
      <aside className="hidden lg:flex flex-col w-[220px] bg-[#18181b] border-r border-zinc-800 flex-shrink-0">
        <div className="flex items-center gap-2.5 px-5 py-4">
          <DazzLogo size={22} className="text-amber-500" />
          <div>
            <div className="font-['Bebas_Neue'] text-[18px] tracking-wide text-zinc-100 leading-tight">DAZZ</div>
            <div className="text-[9px] text-zinc-500">Supplier Portal</div>
          </div>
        </div>

        <nav className="flex-1 px-2 mt-2">
          {NAV_ITEMS.map(item => {
            const active = isActive(item.path);
            return (
              <Link key={item.path} to={item.path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-[5px] mb-[2px] text-[13px] transition-colors ${
                  active
                    ? 'bg-amber-500/[.08] border-l-2 border-amber-500 pl-[10px] text-amber-400'
                    : 'text-zinc-400 hover:bg-zinc-800'
                }`}>
                <item.icon size={15} strokeWidth={1.5} />
                {item.label}
                {item.path === '/notifications' && unread > 0 && (
                  <span className="ml-auto w-2 h-2 rounded-full bg-amber-500" />
                )}
                {item.path === '/documents' && pendingDocs > 0 && (
                  <span className="ml-auto w-2 h-2 rounded-full bg-amber-500" />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto pt-2 border-t border-zinc-800 px-2 pb-3">
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className="w-[30px] h-[30px] rounded-full bg-amber-500 flex items-center justify-center text-[10px] font-bold text-zinc-950 font-['Bebas_Neue'] flex-shrink-0">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-zinc-300 truncate">{supplier?.name || '—'}</div>
              <div className="text-[10px] text-zinc-500 truncate">{supplier?.email || ''}</div>
            </div>
            <button onClick={handleLogout} className="text-zinc-600 hover:text-red-400 transition-colors p-1" title="Logout">
              <LogOut size={14} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </aside>

      {/* ═══ MAIN AREA ═══ */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Topbar — desktop */}
        <header className="hidden lg:flex h-[52px] border-b border-zinc-800 items-center justify-between px-6 flex-shrink-0">
          <div className="font-['Bebas_Neue'] text-[22px] text-zinc-100">
            {NAV_ITEMS.find(i => isActive(i.path))?.label || 'Home'}
          </div>
          <button onClick={() => navigate('/notifications')} className="w-7 h-7 bg-zinc-800 rounded-[7px] flex items-center justify-center relative">
            <Bell size={13} className="text-zinc-400" strokeWidth={1.5} />
            {unread > 0 && <div className="absolute top-[5px] right-[5px] w-[6px] h-[6px] bg-amber-500 rounded-full border-2 border-[#09090b]" />}
          </button>
        </header>

        {/* Mobile header */}
        <header className="lg:hidden px-4 pt-3 pb-2 flex items-center justify-between flex-shrink-0">
          <div className="font-['Bebas_Neue'] text-[26px] tracking-[.07em] text-amber-500">DAZZ</div>
          <div className="flex items-center gap-2">
            <button onClick={() => navigate('/notifications')} className="w-9 h-9 bg-zinc-800 rounded-[7px] flex items-center justify-center relative">
              <Bell size={18} className="text-zinc-400" strokeWidth={1.5} />
              {unread > 0 && <div className="absolute top-[6px] right-[6px] w-[7px] h-[7px] bg-amber-500 rounded-full border-2 border-[#09090b]" />}
            </button>
          </div>
        </header>

        {/* FEAT-06: Pending legal documents banner */}
        {pendingDocs > 0 && pathname !== '/documents' && (
          <Link to="/documents" className="block bg-amber-500/[.08] border-b border-amber-500/20 px-4 py-2.5 hover:bg-amber-500/[.12] transition-colors">
            <div className="flex items-center gap-2 max-w-4xl mx-auto">
              <FileText size={14} className="text-amber-400 flex-shrink-0" />
              <span className="text-amber-400 text-xs">
                You have {pendingDocs} pending legal document{pendingDocs !== 1 ? 's' : ''} to accept.
              </span>
              <span className="text-amber-500 text-xs font-semibold ml-auto">Review now →</span>
            </div>
          </Link>
        )}

        {/* Content */}
        <main className="flex-1 overflow-y-auto pb-[80px] lg:pb-4">
          {children}
        </main>

        {/* Bottom nav — mobile only */}
        <nav className="lg:hidden fixed bottom-0 inset-x-0 bg-[#18181b] border-t border-zinc-800 z-50 flex items-center justify-around h-[64px] px-1.5 pb-[env(safe-area-inset-bottom)]">
          {NAV_ITEMS.map(item => {
            const active = isActive(item.path);
            return (
              <Link key={item.path} to={item.path} className="flex-1 flex flex-col items-center gap-[2px] py-1.5 relative">
                <item.icon size={20} className={active ? 'text-amber-500' : 'text-zinc-600'} strokeWidth={1.5} />
                <span className={`text-[9px] ${active ? 'text-amber-400' : 'text-zinc-600'}`}>{item.label === 'Upload invoice' ? 'Upload' : item.label === 'My profile' ? 'Profile' : item.label}</span>
                {item.path === '/notifications' && unread > 0 && (
                  <span className="absolute top-[2px] right-[6px] w-2 h-2 rounded-full bg-amber-500" />
                )}
                {item.path === '/documents' && pendingDocs > 0 && (
                  <span className="absolute top-[2px] right-[6px] w-2 h-2 rounded-full bg-amber-500" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

export default Layout;
