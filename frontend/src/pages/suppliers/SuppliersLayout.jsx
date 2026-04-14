import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Users, FileText, Bell, UserPlus, FilePlus, FileCheck } from 'lucide-react';
import { getSuppliersDashboard } from '../../services/suppliersApi';
import { useAuth } from '../../context/AuthContext';

const ADMIN_NAV = [
  { path: '/suppliers', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { path: '/suppliers/list', label: 'Proveedores', icon: Users },
  { path: '/suppliers/invoices', label: 'Facturas', icon: FileText },
  { path: '/suppliers/notifications', label: 'Notificaciones', icon: Bell, badgeKey: 'unread_notifications' },
  { path: '/suppliers/documents', label: 'Documentos', icon: FileCheck },
  { path: '/suppliers/autoinvoice', label: 'Autofactura', icon: FilePlus, section: 'add' },
  { path: '/suppliers/invite', label: 'Invitar proveedor', icon: UserPlus, section: 'add' },
];

const BOSS_NAV = [
  { path: '/suppliers/contracts', label: 'Contratos', icon: FileCheck, exact: true },
];

const SuppliersLayout = () => {
  const location = useLocation();
  const { user } = useAuth();
  const isBoss = user?.role === 'BOSS';
  const NAV_ITEMS = isBoss ? BOSS_NAV : ADMIN_NAV;
  const [stats, setStats] = useState({});
  const [fetchError, setFetchError] = useState(false);

  const fetchStats = () => {
    if (isBoss) return; // BOSS doesn't have access to dashboard stats
    getSuppliersDashboard()
      .then(r => { setStats(r.data); setFetchError(false); })
      .catch(() => { setFetchError(true); });
  };

  useEffect(() => {
    fetchStats();
    if (location.pathname !== '/suppliers') return;
    let interval = setInterval(fetchStats, 30000);
    const handleVisibility = () => {
      clearInterval(interval);
      if (document.visibilityState === 'visible') {
        fetchStats();
        interval = setInterval(fetchStats, 30000);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => { clearInterval(interval); document.removeEventListener('visibilitychange', handleVisibility); };
  }, [location.pathname]);

  // BOSS redirect: if at /suppliers index, redirect to /suppliers/contracts
  if (isBoss && location.pathname === '/suppliers') {
    return <Navigate to="/suppliers/contracts" replace />;
  }

  const isActive = (path, exact) => {
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Sidebar — solo desktop */}
      <aside className="hidden lg:flex lg:sticky lg:top-16 lg:h-[calc(100vh-64px)] lg:self-start w-52 bg-zinc-900 border-r border-zinc-800 p-3 flex-col">
        <div className="text-[12px] text-zinc-600 tracking-widest uppercase px-3 mb-1">General</div>

        {NAV_ITEMS.filter(i => !i.section).map(item => {
          const active = isActive(item.path, item.exact);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2.5 px-3 py-2 rounded mb-0.5 transition-all ${
                active
                  ? 'bg-amber-500/10 border-l-2 border-amber-500 pl-2.5 text-amber-400'
                  : 'text-zinc-400 hover:bg-zinc-800'
              }`}
              style={{ fontSize: '0.87em' }}
            >
              <item.icon size={14} className={active ? 'text-amber-500' : 'text-zinc-600'} />
              <span className="flex-1">{item.label}</span>
              {item.badgeKey && stats[item.badgeKey] > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-500" />
              )}
            </Link>
          );
        })}

        <div className="text-[12px] text-zinc-600 tracking-widest uppercase px-3 mt-4 mb-1">Añadir</div>

        {NAV_ITEMS.filter(i => i.section === 'add').map(item => {
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2.5 px-3 py-2 rounded mb-0.5 transition-all ${
                active
                  ? 'bg-amber-500/10 border-l-2 border-amber-500 pl-2.5 text-amber-400'
                  : 'text-zinc-400 hover:bg-zinc-800'
              }`}
              style={{ fontSize: '0.87em' }}
            >
              <item.icon size={14} className={active ? 'text-amber-500' : 'text-zinc-600'} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </aside>

      {/* Content */}
      <main className="flex-1 p-4 sm:p-5 overflow-y-auto bg-zinc-950 pb-24 lg:pb-5">
        {fetchError && (
          <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-[12px] mb-3">
            Error al cargar datos. Comprueba la conexión.
          </div>
        )}
        <Outlet />
      </main>

      {/* Bottom nav — solo móvil (ADMIN: 5 items; BOSS: hidden since only 1 item) */}
      {!isBoss && (
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-zinc-900 border-t border-zinc-800 flex items-center justify-around h-[62px] px-4 safe-area-bottom">
        {NAV_ITEMS.filter(i => i.path !== '/suppliers/invite' && i.path !== '/suppliers/documents').map(item => {
          const active = isActive(item.path, item.exact);
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center justify-center flex-1 py-2 relative"
            >
              <item.icon
                size={26}
                className={active ? 'text-amber-500' : 'text-zinc-600'}
                strokeWidth={active ? 2 : 1.5}
              />
              {item.badgeKey && stats[item.badgeKey] > 0 && (
                <span className="absolute top-1 right-2 w-4.5 h-4.5 min-w-[18px] bg-amber-500 rounded-full text-[9px] font-bold text-zinc-950 flex items-center justify-center">
                  {stats[item.badgeKey]}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      )}
    </div>
  );
};

export default SuppliersLayout;
