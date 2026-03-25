import { useState, useEffect } from 'react';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api';
import { Check, X, DollarSign, FileText, Link2, AlertTriangle, Bell } from 'lucide-react';

const EVENT_ICON = {
  APPROVED:     { icon: Check, cls: 'bg-green-400/10', stroke: 'text-green-400' },
  PAID:         { icon: DollarSign, cls: 'bg-green-400/10', stroke: 'text-green-400' },
  REJECTED:     { icon: X, cls: 'bg-red-400/10', stroke: 'text-red-400' },
  DELETED:      { icon: X, cls: 'bg-red-400/10', stroke: 'text-red-400' },
  NEW_INVOICE:  { icon: FileText, cls: 'bg-blue-400/10', stroke: 'text-blue-400' },
  OC_LINKED:    { icon: Link2, cls: 'bg-purple-400/10', stroke: 'text-purple-400' },
  IA_REJECTED:  { icon: AlertTriangle, cls: 'bg-amber-500/10', stroke: 'text-amber-500' },
  REGISTRATION: { icon: Bell, cls: 'bg-amber-500/10', stroke: 'text-amber-500' },
};

const INVOICE_TYPES = ['NEW_INVOICE', 'APPROVED', 'PAID', 'DELETED', 'OC_LINKED'];
const ACCOUNT_RE = /Data Change|IBAN Change|Deactivation/i;

const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

const Notifications = () => {
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [readFilter, setReadFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const load = () => {
    getNotifications({ limit: 100 })
      .then(r => setNotifs(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const unreadCount = notifs.filter(n => !n.is_read).length;
  const displayed = notifs.filter(n => {
    if (readFilter === 'unread' && n.is_read) return false;
    if (typeFilter === 'all') return true;
    if (typeFilter === 'invoices') return INVOICE_TYPES.includes(n.event_type);
    if (typeFilter === 'account') return n.event_type === 'REGISTRATION' || ACCOUNT_RE.test(n.title);
    return true;
  });

  const handleMarkRead = async (id) => {
    await markNotificationRead(id);
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    setNotifs(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const chipCls = (active) => `text-[11px] px-2.5 py-1 rounded-full transition-colors ${active ? 'bg-amber-500 text-zinc-950 font-semibold' : 'border border-zinc-700 text-zinc-400'}`;

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h1 className="font-['Bebas_Neue'] text-[18px] tracking-wider text-zinc-100">Notifications</h1>
        {unreadCount > 0 && (
          <button onClick={handleMarkAllRead}
            className="text-[12px] bg-zinc-800 border border-zinc-700 text-zinc-300 px-3 py-1.5 rounded-lg hover:bg-zinc-700 transition-colors">
            Mark all as read
          </button>
        )}
      </div>

      {/* Read filter */}
      <div className="flex gap-1.5 mb-2">
        <button onClick={() => setReadFilter('all')} className={chipCls(readFilter === 'all')}>All</button>
        <button onClick={() => setReadFilter('unread')} className={chipCls(readFilter === 'unread')}>Unread ({unreadCount})</button>
      </div>

      {/* Type filter */}
      <div className="flex gap-1.5 mb-3">
        <button onClick={() => setTypeFilter('all')} className={chipCls(typeFilter === 'all')}>All</button>
        <button onClick={() => setTypeFilter('invoices')} className={chipCls(typeFilter === 'invoices')}>Invoices</button>
        <button onClick={() => setTypeFilter('account')} className={chipCls(typeFilter === 'account')}>Account</button>
      </div>

      {/* Info */}
      <div className="text-[12px] text-zinc-400 mb-3">
        {unreadCount > 0 && <><b className="text-amber-400">{unreadCount} unread</b> · </>}
        Archived after 30 days
      </div>

      {/* Notification list */}
      {displayed.length === 0 ? (
        <div className="text-center py-16 text-xs text-zinc-600">No notifications</div>
      ) : (
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] px-3.5">
          {displayed.map(n => {
            const ev = EVENT_ICON[n.event_type] || EVENT_ICON.REGISTRATION;
            const Icon = ev.icon;
            return (
              <div key={n.id}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
                className={`flex items-start gap-2 py-3 border-b border-white/[.04] last:border-0 ${!n.is_read ? 'bg-amber-500/[.02] cursor-pointer' : ''}`}>
                {!n.is_read ? (
                  <div className="w-[7px] h-[7px] rounded-full bg-amber-500 flex-shrink-0 mt-[5px]" />
                ) : (
                  <div className="w-[7px] flex-shrink-0" />
                )}
                <div className={`w-7 h-7 rounded-[7px] flex items-center justify-center flex-shrink-0 ${ev.cls}`}>
                  <Icon size={12} className={ev.stroke} strokeWidth={1.8} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] text-zinc-300">
                    <b>{n.title}</b>{n.message ? ` — ${n.message}` : ''}
                  </div>
                  <div className="text-[11px] text-zinc-600 mt-0.5">{timeAgo(n.created_at)}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Notifications;
