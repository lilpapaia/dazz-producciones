import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Upload, UserPlus, FileText, Trash2, Link2, CreditCard, AlertTriangle, ChevronRight } from 'lucide-react';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../../services/suppliersApi';

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

const SupplierNotifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [visibleCount, setVisibleCount] = useState(50);

  useEffect(() => {
    const doLoad = () => {
      getNotifications({ unread_only: filter === 'unread', limit: 200 })
        .then(r => setNotifications(r.data))
        .catch(() => {})
        .finally(() => setLoading(false));
    };
    setLoading(true);
    doLoad();
    const interval = setInterval(doLoad, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const handleMarkRead = async (id) => {
    await markNotificationRead(id).catch(() => {});
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead().catch(() => {});
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'ahora';
    if (mins < 60) return `${mins}min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;
  const visible = notifications.slice(0, visibleCount);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      {/* Header with actions (N1, N2) */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100">Notificaciones</h1>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="text-[11px] text-zinc-400 border border-zinc-700 px-3 py-1.5 rounded hover:bg-zinc-800 transition-colors">
              Marcar todo leído
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-3.5 items-center">
        <button onClick={() => setFilter('all')} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${filter === 'all' ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'}`}>Todas</button>
        <button onClick={() => setFilter('unread')} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${filter === 'unread' ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'}`}>
          Sin leer {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
        {/* Count bar (N4) */}
        <div className="flex items-center justify-between px-3.5 py-2 bg-zinc-800 text-[11px] text-zinc-400 border-b border-white/[.04]">
          <span><b className="text-amber-400">{unreadCount} sin leer</b> de {notifications.length} notificaciones recientes</span>
          <span className="text-zinc-600">Se archivan a los 30 días</span>
        </div>

        {notifications.length === 0 ? (
          <div className="text-center py-12 text-xs text-zinc-600">
            <Bell size={24} className="mx-auto mb-2 text-zinc-700" />
            Sin notificaciones
          </div>
        ) : (
          visible.map(n => {
            const cfg = EVENT_CONFIG[n.event_type] || { icon: Bell, bg: 'bg-zinc-800', color: 'text-zinc-400' };
            const Icon = cfg.icon;
            // Determine link target (N3)
            const hasSupplier = n.related_supplier_id && n.related_supplier_id > 0;
            return (
              <div
                key={n.id}
                className={`flex items-start gap-2.5 px-3.5 py-3 border-b border-white/[.04] last:border-0 transition-colors ${
                  !n.is_read ? 'bg-amber-500/[.02]' : ''
                }`}
              >
                {!n.is_read ? (
                  <button onClick={() => handleMarkRead(n.id)} className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0 mt-1.5 cursor-pointer hover:bg-amber-400" title="Mark as read" />
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
                {/* View button (N3) */}
                {hasSupplier && (
                  <button
                    onClick={() => { if (!n.is_read) handleMarkRead(n.id); navigate(`/suppliers/${n.related_supplier_id}`); }}
                    className="text-[10px] text-zinc-500 hover:text-zinc-300 border border-zinc-700 px-2 py-1 rounded flex items-center gap-0.5 flex-shrink-0 transition-colors"
                  >
                    Ver <ChevronRight size={10} />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Load more (N2) */}
      {visibleCount < notifications.length && (
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
