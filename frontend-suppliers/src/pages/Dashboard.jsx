import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSummary, getMyInvoices } from '../services/api';

const PILL = {
  PENDING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  OC_PENDING: 'bg-zinc-700/50 text-zinc-400 border-zinc-700',
  APPROVED: 'bg-green-400/10 text-green-400 border-green-400/20',
  PAID: 'bg-green-300/10 text-green-300 border-green-300/20',
  REJECTED: 'bg-red-400/10 text-red-400 border-red-400/20',
  DELETE_REQUESTED: 'bg-red-300/10 text-red-300 border-red-300/20',
};

const Dashboard = () => {
  const { supplier } = useAuth();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getSummary(), getMyInvoices({ limit: 5 })])
      .then(([s, i]) => { setSummary(s.data); setInvoices(i.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="px-4 pt-4">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-3">
        Hello, {supplier?.name?.split(' ')[0] || 'there'}
      </h1>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 border-l-2 border-l-amber-500">
          <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-1">Pending</div>
          <div className="font-['Bebas_Neue'] text-2xl text-amber-500 leading-none">
            {(summary?.pending_amount || 0).toFixed(0)}<span className="text-zinc-500 text-base ml-0.5">EUR</span>
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">To be paid</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
          <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-1">Paid this month</div>
          <div className="font-['Bebas_Neue'] text-2xl text-green-400 leading-none">
            {(summary?.paid_this_month || 0).toFixed(0)}<span className="text-zinc-500 text-base ml-0.5">EUR</span>
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">{summary?.total_invoices || 0} total invoices</div>
        </div>
      </div>

      {/* Recent invoices */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-semibold text-zinc-400 tracking-widest uppercase">Recent invoices</span>
        <button onClick={() => navigate('/invoices')} className="text-[11px] text-amber-400">View all</button>
      </div>

      <div className="space-y-2 mb-4">
        {invoices.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center">
            <p className="text-xs text-zinc-600">No invoices yet</p>
            <button onClick={() => navigate('/upload')} className="mt-2 text-xs text-amber-500 hover:text-amber-400">Upload your first invoice</button>
          </div>
        ) : (
          invoices.map(inv => (
            <div key={inv.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
              <div className="flex items-start justify-between mb-1.5">
                <span className="font-mono text-xs font-medium text-zinc-200">{inv.invoice_number}</span>
                <span className="font-mono text-sm font-semibold text-zinc-100">{inv.final_total.toFixed(2)} EUR</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-zinc-500">{inv.oc_number} &middot; {inv.date}</span>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${PILL[inv.status] || PILL.PENDING}`}>
                  {inv.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Upload CTA */}
      <button
        onClick={() => navigate('/upload')}
        className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-3 rounded-xl transition-colors"
      >
        Upload invoice
      </button>
    </div>
  );
};

export default Dashboard;
