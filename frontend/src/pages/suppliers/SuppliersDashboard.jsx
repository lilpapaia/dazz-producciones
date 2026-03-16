import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Users, CreditCard, Clock, Upload, UserPlus, Trash2, Link2, AlertTriangle, Bell } from 'lucide-react';
import { getSuppliersDashboard, getNotifications } from '../../services/suppliersApi';

const FEED_ICONS = {
  NEW_INVOICE: { icon: Upload, bg: 'bg-blue-400/10', color: 'text-blue-400' },
  REGISTRATION: { icon: UserPlus, bg: 'bg-green-400/10', color: 'text-green-400' },
  APPROVED: { icon: FileText, bg: 'bg-green-400/10', color: 'text-green-400' },
  PAID: { icon: CreditCard, bg: 'bg-green-300/10', color: 'text-green-300' },
  REJECTED: { icon: FileText, bg: 'bg-red-400/10', color: 'text-red-400' },
  DELETED: { icon: Trash2, bg: 'bg-red-400/10', color: 'text-red-400' },
  OC_LINKED: { icon: Link2, bg: 'bg-purple-400/10', color: 'text-purple-400' },
  IA_REJECTED: { icon: AlertTriangle, bg: 'bg-amber-500/10', color: 'text-amber-500' },
};

const SuppliersDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getSuppliersDashboard(),
      getNotifications({ limit: 10 }),
    ]).then(([statsRes, feedRes]) => {
      setStats(statsRes.data);
      setFeed(feedRes.data);
    }).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const kpis = [
    { label: 'Pending invoices', value: stats?.pending_invoices || 0, sub: 'Awaiting review', accent: true, warn: true },
    { label: 'Approved this month', value: stats?.approved_this_month || 0, sub: `${stats?.pending_invoices || 0} still pending` },
    { label: 'Active suppliers', value: stats?.active_suppliers || 0, sub: 'Registered on portal', ok: true },
    { label: 'Total paid', value: `${((stats?.total_paid_this_month || 0) / 1000).toFixed(1)}K`, sub: 'This month (EUR)', suffix: true },
  ];

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}min ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div>
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-4">Dashboard</h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 mb-4">
        {kpis.map((kpi, i) => (
          <div key={i} className={`bg-zinc-900 border border-zinc-800 rounded-md p-3.5 ${kpi.accent ? 'border-l-2 border-l-amber-500' : ''}`}>
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-1.5">{kpi.label}</div>
            <div className={`font-['Bebas_Neue'] text-2xl tracking-wide leading-none ${kpi.warn ? 'text-amber-500' : kpi.ok ? 'text-green-400' : 'text-zinc-100'}`}>
              {kpi.value}{kpi.suffix && <span className="text-zinc-500 text-lg ml-0.5">EUR</span>}
            </div>
            <div className="text-[10px] text-zinc-500 mt-1">{kpi.sub}</div>
          </div>
        ))}
      </div>

      {/* Two columns */}
      <div className="grid lg:grid-cols-2 gap-3">
        {/* Activity feed */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
          <div className="font-['Bebas_Neue'] text-sm tracking-wider text-zinc-300 mb-3">Recent activity</div>
          {feed.length === 0 ? (
            <p className="text-xs text-zinc-600">No recent activity</p>
          ) : (
            feed.slice(0, 6).map(n => {
              const cfg = FEED_ICONS[n.event_type] || { icon: Bell, bg: 'bg-zinc-800', color: 'text-zinc-400' };
              const Icon = cfg.icon;
              return (
                <div key={n.id} className="flex items-start gap-2.5 py-2.5 border-b border-white/[.04] last:border-0">
                  <div className={`w-[30px] h-[30px] rounded flex items-center justify-center flex-shrink-0 ${cfg.bg}`}>
                    <Icon size={13} className={cfg.color} strokeWidth={1.8} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs text-zinc-300 leading-snug">{n.message || n.title}</div>
                    <div className="text-[10px] text-zinc-600 mt-0.5">
                      {timeAgo(n.created_at)}
                      {!n.is_read && <b className="text-amber-400 ml-2">unread</b>}
                    </div>
                  </div>
                </div>
              );
            })
          )}
          {feed.length > 6 && (
            <button onClick={() => navigate('/suppliers/notifications')} className="text-[11px] text-amber-500 hover:text-amber-400 mt-2">
              View all notifications
            </button>
          )}
        </div>

        {/* Invoice status chart */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
          <div className="font-['Bebas_Neue'] text-sm tracking-wider text-zinc-300 mb-3">Invoice status</div>
          <div className="flex flex-col gap-2.5 mt-1">
            {[
              { label: 'Pending', value: stats?.pending_invoices || 0, color: 'bg-amber-500', text: 'text-amber-400' },
              { label: 'Approved', value: stats?.approved_this_month || 0, color: 'bg-green-400', text: 'text-green-400' },
              { label: 'Paid', value: stats?.total_paid_this_month > 0 ? Math.ceil(stats.total_paid_this_month / 100) : 0, color: 'bg-green-300', text: 'text-green-300' },
            ].map((s, i) => {
              const maxVal = Math.max(...[stats?.pending_invoices || 0, stats?.approved_this_month || 0, 10]);
              const pct = maxVal > 0 ? Math.min((s.value / maxVal) * 100, 100) : 0;
              return (
                <div key={i} className="flex items-center gap-2.5 text-xs">
                  <div className={`w-2 h-2 rounded-sm ${s.color} flex-shrink-0`} />
                  <span className="flex-1 text-zinc-400">{s.label}</span>
                  <span className={`font-mono text-[11px] ${s.text}`}>{s.value}</span>
                  <div className="w-20 h-1 bg-zinc-800 rounded">
                    <div className={`h-full rounded ${s.color}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuppliersDashboard;
