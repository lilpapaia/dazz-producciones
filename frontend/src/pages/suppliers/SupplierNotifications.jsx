import { useState, useEffect } from 'react';
import { Bell, Upload, UserPlus, FileText, Trash2, Link2, CreditCard } from 'lucide-react';
import { getNotifications, markNotificationRead } from '../../services/suppliersApi';

const EVENT_CONFIG = {
  NEW_INVOICE: { icon: Upload, bg: 'bg-blue-400/10', color: 'text-blue-400' },
  REGISTRATION: { icon: UserPlus, bg: 'bg-green-400/10', color: 'text-green-400' },
  APPROVED: { icon: FileText, bg: 'bg-green-400/10', color: 'text-green-400' },
  PAID: { icon: CreditCard, bg: 'bg-green-300/10', color: 'text-green-300' },
  REJECTED: { icon: FileText, bg: 'bg-red-400/10', color: 'text-red-400' },
  DELETED: { icon: Trash2, bg: 'bg-red-400/10', color: 'text-red-400' },
  OC_LINKED: { icon: Link2, bg: 'bg-purple-400/10', color: 'text-purple-400' },
  IA_REJECTED: { icon: Bell, bg: 'bg-amber-500/10', color: 'text-amber-500' },
};

const SupplierNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'unread'

  const load = () => {
    getNotifications({ unread_only: filter === 'unread', limit: 50 })
      .then(r => setNotifications(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { setLoading(true); load(); }, [filter]);

  // Poll every 30s
  useEffect(() => {
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const handleMarkRead = async (id) => {
    await markNotificationRead(id).catch(() => {});
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}min ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-4">Notifications</h1>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-3.5 items-center">
        <button onClick={() => setFilter('all')} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${filter === 'all' ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'}`}>
          All
        </button>
        <button onClick={() => setFilter('unread')} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${filter === 'unread' ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'}`}>
          Unread {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
        {unreadCount > 0 && filter === 'all' && (
          <div className="flex items-center justify-between px-3.5 py-2 bg-zinc-800 text-[11px] text-zinc-400 border-b border-white/[.04]">
            <span>{unreadCount} unread notification{unreadCount !== 1 && 's'}</span>
          </div>
        )}

        {notifications.length === 0 ? (
          <div className="text-center py-12 text-xs text-zinc-600">
            <Bell size={24} className="mx-auto mb-2 text-zinc-700" />
            No notifications
          </div>
        ) : (
          notifications.map(n => {
            const cfg = EVENT_CONFIG[n.event_type] || EVENT_CONFIG.NEW_INVOICE;
            const Icon = cfg.icon;
            return (
              <div
                key={n.id}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
                className={`flex items-start gap-2.5 px-3.5 py-3 border-b border-white/[.04] last:border-0 transition-colors ${!n.is_read ? 'bg-amber-500/[.02] cursor-pointer hover:bg-amber-500/[.04]' : ''}`}
              >
                {!n.is_read ? (
                  <div className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0 mt-1.5" />
                ) : (
                  <div className="w-2 h-2 flex-shrink-0 mt-1.5" />
                )}
                <div className={`w-7 h-7 rounded flex items-center justify-center flex-shrink-0 ${cfg.bg}`}>
                  <Icon size={13} className={cfg.color} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-zinc-300 leading-snug">
                    <span className="font-medium">{n.title}</span>
                    {n.message && <span className="text-zinc-400"> &mdash; {n.message}</span>}
                  </div>
                  <div className="text-[10px] text-zinc-600 mt-0.5">{timeAgo(n.created_at)}</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default SupplierNotifications;
