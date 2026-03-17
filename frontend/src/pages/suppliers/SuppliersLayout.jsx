import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, FileText, Bell, UserPlus, Menu } from 'lucide-react';
import { getSuppliersDashboard, getNotifications } from '../../services/suppliersApi';

const NAV_ITEMS = [
  { path: '/suppliers', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { path: '/suppliers/list', label: 'Proveedores', icon: Users },
  { path: '/suppliers/invoices', label: 'Facturas', icon: FileText },
  { path: '/suppliers/notifications', label: 'Notificaciones', icon: Bell, badgeKey: 'unread_notifications' },
  { path: '/suppliers/invite', label: 'Invitar proveedor', icon: UserPlus, section: 'add' },
];

const SuppliersLayout = () => {
  const location = useLocation();
  const [stats, setStats] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchStats = () => getSuppliersDashboard().then(r => setStats(r.data)).catch(() => {});

  useEffect(() => { fetchStats(); }, [location.pathname]);
  useEffect(() => {
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const isActive = (path, exact) => {
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Mobile toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed bottom-4 right-4 z-50 bg-amber-500 text-zinc-950 p-3 rounded-full shadow-lg shadow-amber-500/30"
      >
        <Menu size={20} />
      </button>

      {/* Sidebar */}
      <aside className={`
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40
        w-52 bg-zinc-900 border-r border-zinc-800 p-3 flex flex-col
        transition-transform lg:transition-none pt-20 lg:pt-3
      `}>
        <div className="text-[9px] text-zinc-600 tracking-widest uppercase px-3 mb-1">General</div>

        {NAV_ITEMS.filter(i => !i.section).map(item => {
          const active = isActive(item.path, item.exact);
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs mb-0.5 transition-all ${
                active
                  ? 'bg-amber-500/10 border-l-2 border-amber-500 pl-2.5 text-amber-400'
                  : 'text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              <item.icon size={14} className={active ? 'text-amber-500' : 'text-zinc-600'} />
              <span className="flex-1">{item.label}</span>
              {item.badgeKey && stats[item.badgeKey] > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-500" />
              )}
            </Link>
          );
        })}

        <div className="text-[9px] text-zinc-600 tracking-widest uppercase px-3 mt-4 mb-1">Añadir</div>

        {NAV_ITEMS.filter(i => i.section === 'add').map(item => {
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-xs mb-0.5 transition-all ${
                active
                  ? 'bg-amber-500/10 border-l-2 border-amber-500 pl-2.5 text-amber-400'
                  : 'text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              <item.icon size={14} className={active ? 'text-amber-500' : 'text-zinc-600'} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/60 z-30" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Content */}
      <main className="flex-1 p-4 sm:p-5 overflow-y-auto bg-zinc-950">
        <Outlet />
      </main>
    </div>
  );
};

export default SuppliersLayout;
