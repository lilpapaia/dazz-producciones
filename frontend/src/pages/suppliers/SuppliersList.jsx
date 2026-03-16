import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronRight } from 'lucide-react';
import { getSuppliers } from '../../services/suppliersApi';
import { getCompanies } from '../../services/api';

const TYPE_BADGE = {
  INFLUENCER: 'bg-purple-400/10 text-purple-400 border border-purple-400/20',
  GENERAL: 'bg-blue-400/10 text-blue-400 border border-blue-400/20',
  MIXED: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
};
const STATUS_BADGE = {
  ACTIVE: 'bg-green-400/10 text-green-400 border border-green-400/20',
  NEW: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  DEACTIVATED: 'bg-zinc-700/50 text-zinc-500 border border-zinc-700',
};

const timeAgo = (dateStr) => {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
};

const SuppliersList = () => {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState(null);

  const load = () => {
    const params = {};
    if (companyFilter) params.company_id = companyFilter;
    Promise.all([getSuppliers(params), getCompanies()])
      .then(([s, c]) => { setSuppliers(s.data); setCompanies(c.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { setLoading(true); load(); }, [companyFilter]);

  const filtered = suppliers.filter(s => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || (s.nif_cif || '').toLowerCase().includes(q);
  });

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100">Suppliers</h1>
        <button onClick={() => navigate('/suppliers/invite')} className="bg-amber-500 hover:bg-amber-400 text-zinc-950 text-xs font-semibold px-4 py-2 rounded transition-colors">
          + Invite supplier
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2.5 mb-3.5 flex-wrap items-center">
        <div className="relative max-w-[240px] flex-1">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
          <input
            placeholder="Search by name or NIF..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[11px] pl-8 pr-3 py-2 rounded focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none"
          />
        </div>
        <span className="text-[9px] text-zinc-500 tracking-widest uppercase">Company:</span>
        <button onClick={() => setCompanyFilter(null)} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${!companyFilter ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}>All</button>
        {companies.map(c => (
          <button key={c.id} onClick={() => setCompanyFilter(c.id)} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${companyFilter === c.id ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}>
            {c.name.length > 15 ? c.name.slice(0, 15) + '...' : c.name}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-x-auto">
        <table className="w-full min-w-[700px]">
          <thead>
            <tr>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium w-5"></th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Supplier</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">NIF/CIF</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Type</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Company</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Status</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">OC</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Last activity</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium w-16"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(s => (
              <tr key={s.id} onClick={() => navigate(`/suppliers/${s.id}`)} className="cursor-pointer hover:bg-white/[.02] transition-colors">
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  {s.pending_invoices > 0 && <div className="w-2 h-2 rounded-full bg-amber-500" />}
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <div className="text-xs font-medium text-zinc-200">{s.name}</div>
                  <div className="text-[10px] text-zinc-500">{s.email}</div>
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04] text-xs text-zinc-400 font-mono">{s.nif_cif || '—'}</td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${TYPE_BADGE[s.supplier_type] || TYPE_BADGE.GENERAL}`}>{s.supplier_type}</span>
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04] text-[11px] text-zinc-400">{s.company_name || 'All'}</td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${STATUS_BADGE[s.status] || STATUS_BADGE.NEW}`}>{s.status}</span>
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  {s.oc_number ? (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/[.08] text-amber-400 font-semibold font-mono border border-amber-500/15">{s.oc_number}</span>
                  ) : <span className="text-[11px] text-zinc-600">—</span>}
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04] text-[11px] text-zinc-500">{timeAgo(s.last_activity)}</td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <button className="text-[11px] text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors">
                    View <ChevronRight size={12} />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan="9" className="text-center py-8 text-xs text-zinc-600">No suppliers found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SuppliersList;
