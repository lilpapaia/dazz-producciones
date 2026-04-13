import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification, deleteReadNotifications } from '../services/api';
import { Check, X, DollarSign, FileText, Link2, AlertTriangle, Bell, Trash2 } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';

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

const INVOICE_TYPES = ['NEW_INVOICE', 'APPROVED', 'PAID', 'DELETED', 'OC_LINKED', 'IA_REJECTED', 'REJECTED'];
const ACCOUNT_RE = /Data Change|IBAN Change|Deactivation/i;

const getNotifDestination = (n) => {
  if (INVOICE_TYPES.includes(n.event_type) && !ACCOUNT_RE.test(n.title)) return '/';
  if (n.event_type === 'REGISTRATION' || ACCOUNT_RE.test(n.title)) return '/profile';
  return '/';
};

const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z').getTime();
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
  const navigate = useNavigate();
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [readFilter, setReadFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [confirmClearRead, setConfirmClearRead] = useState(false);

  const load = () => {
    getNotifications({ limit: 100 })
      .then(r => setNotifs(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const unreadCount = notifs.filter(n => !n.is_read).length;
  const readCount = notifs.filter(n => n.is_read).length;
  const displayed = notifs.filter(n => {
    if (readFilter === 'unread' && n.is_read) return false;
    if (typeFilter === 'all') return true;
    if (typeFilter === 'invoices') return INVOICE_TYPES.includes(n.event_type) && !ACCOUNT_RE.test(n.title);
    if (typeFilter === 'account') return n.event_type === 'REGISTRATION' || ACCOUNT_RE.test(n.title);
    return true;
  });

  const handleClick = async (n) => {
    if (!n.is_read) {
      setNotifs(prev => prev.map(x => x.id === n.id ? { ...x, is_read: true } : x));
      try { await markNotificationRead(n.id); } catch {
        setNotifs(prev => prev.map(x => x.id === n.id ? { ...x, is_read: false } : x));
        return;
      }
    }
    navigate(getNotifDestination(n));
  };

  const handleMarkAllRead = async () => {
    const snapshot = notifs;
    setNotifs(prev => prev.map(n => ({ ...n, is_read: true })));
    try { await markAllNotificationsRead(); } catch { setNotifs(snapshot); }
  };

  const handleDeleteOne = async (e, id) => {
    e.stopPropagation();
    setNotifs(prev => prev.filter(n => n.id !== id));
    try { await deleteNotification(id); } catch { load(); }
  };

  const handleClearRead = async () => {
    const snapshot = notifs;
    setNotifs(prev => prev.filter(n => !n.is_read));
    try { await deleteReadNotifications(); } catch { setNotifs(snapshot); }
  };

  const chipCls = (active) => `text-[11px] px-2.5 py-1 rounded-full transition-colors ${active ? 'bg-amber-500 text-zinc-950 font-semibold' : 'border border-zinc-700 text-zinc-400'}`;

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="max-w-2xl lg:max-w-4xl mx-auto px-4 lg:px-6 pt-4 lg:pt-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 lg:mb-5">
        <h1 className="font-['Bebas_Neue'] text-[18px] lg:text-[22px] tracking-wider text-zinc-100">Notifications</h1>
        <div className="flex gap-2">
          {readCount > 0 && (
            <button onClick={() => setConfirmClearRead(true)}
              className="text-[12px] bg-zinc-800 border border-zinc-700 text-red-400 px-3 py-1.5 rounded-lg hover:bg-red-500/10 hover:border-red-500/30 transition-colors">
              Clear read
            </button>
          )}
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead}
              className="text-[12px] bg-zinc-800 border border-zinc-700 text-zinc-300 px-3 py-1.5 rounded-lg hover:bg-zinc-700 transition-colors">
              Mark all as read
            </button>
          )}
        </div>
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
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] px-3.5 lg:px-5 overflow-hidden">
          {displayed.map(n => {
            const ev = EVENT_ICON[n.event_type] || EVENT_ICON.REGISTRATION;
            const Icon = ev.icon;
            return (
              <div key={n.id}
                onClick={() => handleClick(n)}
                className={`flex items-start gap-2 py-3 lg:py-4 border-b border-white/[.04] last:border-0 cursor-pointer group ${!n.is_read ? 'bg-amber-500/[.02] -mx-3.5 px-3.5 lg:-mx-5 lg:px-5' : ''}`}>
                {!n.is_read ? (
                  <div className="w-[7px] h-[7px] rounded-full bg-amber-500 flex-shrink-0 mt-[5px]" />
                ) : (
                  <div className="w-[7px] flex-shrink-0" />
                )}
                <div className={`w-7 h-7 lg:w-8 lg:h-8 rounded-[7px] flex items-center justify-center flex-shrink-0 ${ev.cls}`}>
                  <Icon size={12} className={ev.stroke} strokeWidth={1.8} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] lg:text-[14px] text-zinc-300">
                    <b>{n.title}</b>{n.message ? ` — ${n.message}` : ''}
                  </div>
                  <div className="text-[11px] text-zinc-600 mt-0.5">{timeAgo(n.created_at)}</div>
                </div>
                {n.is_read && (
                  <button onClick={(e) => handleDeleteOne(e, n.id)}
                    className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 p-1.5 text-zinc-600 hover:text-red-400 transition-all flex-shrink-0"
                    title="Delete notification">
                    <Trash2 size={14} strokeWidth={1.5} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmClearRead}
        onClose={() => setConfirmClearRead(false)}
        onConfirm={handleClearRead}
        title="Clear read notifications"
        message={`This will permanently delete ${readCount} read notification${readCount !== 1 ? 's' : ''}. Unread notifications will not be affected.`}
        confirmText="Clear read"
        cancelText="Cancel"
        type="danger"
      />
    </div>
  );
};

export default Notifications;
