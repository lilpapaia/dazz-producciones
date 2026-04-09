import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Upload, UserPlus, FileText, Trash2, Link2, CreditCard, AlertTriangle } from 'lucide-react';
import { getNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification, deleteReadNotifications } from '../../services/suppliersApi';

const EVENT_CONFIG = {
  NEW_INVOICE: { icon: Upload, bg: 'bg-blue-400/10', color: 'text-blue-400' },
  REGISTRATION: { icon: UserPlus, bg: 'bg-green-400/10', color: 'text-green-400' },
  APPROVED: { icon: FileText, bg: 'bg-green-400/10', color: 'text-green-400' },
  PAID: { icon: CreditCard, bg: 'bg-green-300/10', color: 'text-green-300' },
  REJECTED: { icon: FileText, bg: 'bg-red-400/10', color: 'text-red-400' },
  DELETED: { icon: Trash2, bg: 'bg-red-400/10', color: 'text-red-400' },
  OC_LINKED: { icon: Link2, bg: 'bg-purple-400/10', color: 'text-purple-400' },
  IA_REJECTED: { icon: AlertTriangle, bg: 'bg-amber-500/10', color: 'text-amber-500' },
};

const INVOICE_TYPES = ['NEW_INVOICE', 'APPROVED', 'PAID', 'DELETED', 'OC_LINKED'];
const ACCOUNT_RE = /Data Change|IBAN Change|Deactivation/i;

const getRoute = (n) => {
  // Invoice-centric events → invoice detail
  if (['NEW_INVOICE', 'OC_LINKED', 'DELETED'].includes(n.event_type) && n.related_invoice_id) {
    return `/suppliers/invoices/${n.related_invoice_id}?from=notifications`;
  }
  // REJECTED / IA_REJECTED with invoice → invoice detail
  if ((n.event_type === 'REJECTED' || n.event_type === 'IA_REJECTED') && n.related_invoice_id) {
    return `/suppliers/invoices/${n.related_invoice_id}?from=notifications`;
  }
  // Supplier-centric → supplier detail
  if (n.related_supplier_id && n.related_supplier_id > 0) {
    return `/suppliers/${n.related_supplier_id}`;
  }
  // No navigable destination (#3-6 IA_REJECTED cert without supplier_id)
  return null;
};

const SupplierNotifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [readFilter, setReadFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [visibleCount, setVisibleCount] = useState(50);

  useEffect(() => {
    const doLoad = () => {
      getNotifications({ limit: 200 })
        .then(r => setNotifications(r.data))
        .catch(() => {})
        .finally(() => setLoading(false));
    };
    setLoading(true);
    doLoad();
    // PERF-8: Poll every 60s, pause when tab not visible
    let interval = setInterval(doLoad, 60000);
    const handleVisibility = () => {
      clearInterval(interval);
      if (document.visibilityState === 'visible') {
        doLoad();
        interval = setInterval(doLoad, 60000);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => { clearInterval(interval); document.removeEventListener('visibilitychange', handleVisibility); };
  }, []);

  const handleMarkRead = async (id) => {
    await markNotificationRead(id).catch(() => {});
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead().catch(() => {});
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const handleDelete = async (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    await deleteNotification(id).catch(() => {});
  };

  const handleDeleteRead = async () => {
    setNotifications(prev => prev.filter(n => !n.is_read));
    await deleteReadNotifications().catch(() => {});
  };

  const handleClick = (n) => {
    const route = getRoute(n);
    if (!route) return;
    if (!n.is_read) handleMarkRead(n.id);
    navigate(route);
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z').getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'ahora';
    if (mins < 60) return `${mins}min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;
  const readCount = notifications.filter(n => n.is_read).length;
  const displayed = notifications.filter(n => {
    if (readFilter === 'unread' && n.is_read) return false;
    if (typeFilter === 'all') return true;
    if (typeFilter === 'invoices') return INVOICE_TYPES.includes(n.event_type);
    if (typeFilter === 'ia') return n.event_type === 'IA_REJECTED';
    if (typeFilter === 'account') return n.event_type === 'REGISTRATION' || ACCOUNT_RE.test(n.title);
    return true;
  });
  const visible = displayed.slice(0, visibleCount);

  const chipCls = (active) => `text-[11px] px-3 py-1 rounded-full border transition-all ${active ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'}`;

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      {/* Header with actions */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">Notificaciones</h1>
        <div className="flex gap-2">
          {readCount > 0 && (
            <button onClick={handleDeleteRead} className="text-[11px] text-red-400 border border-red-400/25 px-3 py-1.5 rounded hover:bg-red-400/10 transition-colors flex items-center gap-1">
              <Trash2 size={11} /> Limpiar leídas ({readCount})
            </button>
          )}
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="text-[11px] text-zinc-400 border border-zinc-700 px-3 py-1.5 rounded hover:bg-zinc-800 transition-colors">
              Marcar todo leído
            </button>
          )}
        </div>
      </div>

      {/* Read filter */}
      <div className="flex gap-2 mb-2 items-center">
        <button onClick={() => setReadFilter('all')} className={chipCls(readFilter === 'all')}>Todas</button>
        <button onClick={() => setReadFilter('unread')} className={chipCls(readFilter === 'unread')}>
          Sin leer {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      {/* Type filter */}
      <div className="flex gap-2 mb-3.5 items-center">
        <button onClick={() => setTypeFilter('all')} className={chipCls(typeFilter === 'all')}>Todas</button>
        <button onClick={() => setTypeFilter('invoices')} className={chipCls(typeFilter === 'invoices')}>Facturas</button>
        <button onClick={() => setTypeFilter('ia')} className={chipCls(typeFilter === 'ia')}>IA</button>
        <button onClick={() => setTypeFilter('account')} className={chipCls(typeFilter === 'account')}>Cuenta</button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
        {/* Count bar */}
        <div className="flex items-center justify-between px-3.5 py-2 bg-zinc-800 text-[11px] text-zinc-400 border-b border-white/[.04]">
          <span><b className="text-amber-400">{unreadCount} sin leer</b> de {displayed.length} notificaciones</span>
          <span className="text-zinc-400">Se archivan a los 30 días</span>
        </div>

        {displayed.length === 0 ? (
          <div className="text-center py-12 text-xs text-zinc-600">
            <Bell size={24} className="mx-auto mb-2 text-zinc-700" />
            Sin notificaciones
          </div>
        ) : (
          visible.map(n => {
            const cfg = EVENT_CONFIG[n.event_type] || { icon: Bell, bg: 'bg-zinc-800', color: 'text-zinc-400' };
            const Icon = cfg.icon;
            const route = getRoute(n);
            const isClickable = !!route;
            return (
              <div
                key={n.id}
                onClick={() => isClickable && handleClick(n)}
                className={`flex items-start gap-2.5 px-3.5 py-3 border-b border-white/[.04] last:border-0 transition-colors ${
                  !n.is_read ? 'bg-amber-500/[.02]' : ''
                } ${isClickable ? 'cursor-pointer hover:bg-zinc-800/50' : 'cursor-default'}`}
              >
                {!n.is_read ? (
                  <button onClick={(e) => { e.stopPropagation(); handleMarkRead(n.id); }} className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0 mt-1.5 cursor-pointer hover:bg-amber-400" title="Marcar leída" />
                ) : (
                  <div className="w-2 h-2 flex-shrink-0 mt-1.5" />
                )}
                <div className={`w-[30px] h-[30px] rounded flex items-center justify-center flex-shrink-0 ${cfg.bg}`}>
                  <Icon size={13} className={cfg.color} strokeWidth={1.8} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-zinc-300 leading-snug">
                    <span className="font-medium">{n.title}</span>
                    {n.message && <span className="text-zinc-400"> — {n.message}</span>}
                  </div>
                  <div className="text-[10px] text-zinc-600 mt-0.5">
                    {timeAgo(n.created_at)}
                    {!n.is_read && <b className="text-amber-400 ml-2">sin leer</b>}
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(n.id); }}
                  className="w-[26px] h-[26px] flex items-center justify-center rounded text-zinc-600 hover:text-red-400 hover:bg-red-400/10 transition-colors flex-shrink-0"
                  title="Eliminar"
                >
                  <Trash2 size={12} strokeWidth={1.5} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Load more */}
      {visibleCount < displayed.length && (
        <div className="text-center mt-3">
          <button onClick={() => setVisibleCount(v => v + 50)} className="text-[11px] text-amber-500 hover:text-amber-400">
            Ver historial completo →
          </button>
        </div>
      )}
    </div>
  );
};

export default SupplierNotifications;
