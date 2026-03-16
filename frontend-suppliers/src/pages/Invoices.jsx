import { useState, useEffect } from 'react';
import { Search, Trash2, ExternalLink } from 'lucide-react';
import { getMyInvoices, requestDeleteInvoice } from '../services/api';

const PILL = {
  PENDING: { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500' },
  OC_PENDING: { cls: 'bg-zinc-700/50 text-zinc-400 border-zinc-700', dot: 'bg-zinc-500' },
  APPROVED: { cls: 'bg-green-400/10 text-green-400 border-green-400/20', dot: 'bg-green-400' },
  PAID: { cls: 'bg-green-300/10 text-green-300 border-green-300/20', dot: 'bg-green-300' },
  REJECTED: { cls: 'bg-red-400/10 text-red-400 border-red-400/20', dot: 'bg-red-400' },
  DELETE_REQUESTED: { cls: 'bg-red-300/10 text-red-300 border-red-300/20', dot: 'bg-red-300' },
};

const Invoices = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState(null);
  const [deleteModal, setDeleteModal] = useState(null);
  const [reason, setReason] = useState('');

  const load = () => {
    const params = {};
    if (statusFilter) params.status = statusFilter;
    getMyInvoices(params)
      .then(r => setInvoices(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { setLoading(true); load(); }, [statusFilter]);

  const filtered = invoices.filter(inv => {
    if (!search) return true;
    const q = search.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) || inv.oc_number?.toLowerCase().includes(q);
  });

  const handleDelete = async () => {
    if (!deleteModal || !reason.trim()) return;
    try {
      await requestDeleteInvoice(deleteModal.id, reason);
      setDeleteModal(null);
      setReason('');
      load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error');
    }
  };

  const canDelete = (status) => ['PENDING', 'OC_PENDING'].includes(status);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="px-4 pt-4">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-3">My invoices</h1>

      {/* Search */}
      <div className="relative mb-3">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
        <input
          placeholder="Search invoice or OC..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs pl-9 pr-3 py-2.5 rounded-xl focus:border-amber-500 outline-none"
        />
      </div>

      {/* Filter chips */}
      <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1 scrollbar-none">
        {[null, 'PENDING', 'APPROVED', 'PAID', 'REJECTED'].map(s => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`text-[11px] px-3 py-1.5 rounded-full border transition-all whitespace-nowrap flex-shrink-0 ${
              statusFilter === s ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Invoice list */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-10 text-xs text-zinc-600">No invoices found</div>
        ) : (
          filtered.map(inv => {
            const pill = PILL[inv.status] || PILL.PENDING;
            return (
              <div key={inv.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
                <div className="flex items-start justify-between mb-1.5">
                  <div className="font-mono text-xs font-medium text-zinc-200 flex items-center gap-1.5">
                    {inv.invoice_number}
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${pill.cls}`}>
                      <span className={`w-1 h-1 rounded-full ${pill.dot}`} />{inv.status}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-semibold text-zinc-100">{inv.final_total.toFixed(2)} EUR</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500">{inv.oc_number} &middot; {inv.date}</span>
                  <div className="flex gap-1">
                    {inv.file_url && (
                      <button onClick={() => window.open(inv.file_url, '_blank')} className="p-1 text-zinc-500 hover:text-zinc-300 transition-colors" title="View PDF">
                        <ExternalLink size={14} />
                      </button>
                    )}
                    {canDelete(inv.status) && (
                      <button onClick={() => setDeleteModal(inv)} className="p-1 text-red-400/60 hover:text-red-400 transition-colors" title="Request deletion">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
                {inv.rejection_reason && (
                  <div className="mt-2 text-[10px] text-red-400 bg-red-400/[.06] border border-red-400/[.12] rounded p-2">
                    Rejected: {inv.rejection_reason}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Delete modal */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-end sm:items-center justify-center" onClick={() => { setDeleteModal(null); setReason(''); }}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-t-2xl sm:rounded-xl w-full sm:w-[400px] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">Request deletion</h3>
            <p className="text-xs text-zinc-500 mb-3">Invoice {deleteModal.invoice_number}</p>
            <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1.5 block">Reason <span className="text-amber-500">*</span></label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              placeholder="Why do you want to delete this invoice?"
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded-md focus:border-amber-500 outline-none resize-none mb-3"
            />
            <div className="flex gap-2">
              <button onClick={() => { setDeleteModal(null); setReason(''); }} className="flex-1 text-xs py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancel</button>
              <button onClick={handleDelete} disabled={!reason.trim()} className="flex-1 bg-red-500 hover:bg-red-400 text-white font-semibold text-xs py-2.5 rounded-md transition-colors disabled:opacity-40">Request deletion</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Invoices;
