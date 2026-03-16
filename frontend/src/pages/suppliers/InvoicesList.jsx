import { useState, useEffect } from 'react';
import { Search, List, Columns3, ExternalLink, Check, X, CreditCard } from 'lucide-react';
import { getAllInvoices, updateInvoiceStatus, deleteInvoice } from '../../services/suppliersApi';
import { getCompanies } from '../../services/api';

const PILL = {
  PENDING: { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500' },
  OC_PENDING: { cls: 'bg-zinc-700/50 text-zinc-400 border-zinc-700', dot: 'bg-zinc-500' },
  APPROVED: { cls: 'bg-green-400/10 text-green-400 border-green-400/20', dot: 'bg-green-400' },
  PAID: { cls: 'bg-green-300/10 text-green-300 border-green-300/20', dot: 'bg-green-300' },
  REJECTED: { cls: 'bg-red-400/10 text-red-400 border-red-400/20', dot: 'bg-red-400' },
  DELETE_REQUESTED: { cls: 'bg-red-300/10 text-red-300 border-red-300/20', dot: 'bg-red-300' },
};

const KANBAN_COLS = ['PENDING', 'APPROVED', 'PAID', 'REJECTED'];

const InvoicesList = () => {
  const [invoices, setInvoices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list');
  const [statusFilter, setStatusFilter] = useState(null);
  const [search, setSearch] = useState('');
  const [actionModal, setActionModal] = useState(null); // { invoice, action }
  const [reason, setReason] = useState('');

  const load = () => {
    const params = {};
    if (statusFilter) params.status = statusFilter;
    Promise.all([getAllInvoices(params), getCompanies()])
      .then(([inv, c]) => { setInvoices(inv.data); setCompanies(c.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [statusFilter]);

  const filtered = invoices.filter(inv => {
    if (!search) return true;
    const q = search.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) ||
      inv.supplier_name?.toLowerCase().includes(q) ||
      inv.oc_number?.toLowerCase().includes(q);
  });

  const handleAction = async () => {
    if (!actionModal) return;
    const { invoice, action } = actionModal;
    try {
      if (action === 'approve') {
        await updateInvoiceStatus(invoice.id, { status: 'APPROVED' });
      } else if (action === 'pay') {
        await updateInvoiceStatus(invoice.id, { status: 'PAID' });
      } else if (action === 'reject') {
        if (!reason.trim()) return;
        await updateInvoiceStatus(invoice.id, { status: 'REJECTED', reason });
      } else if (action === 'delete') {
        await deleteInvoice(invoice.id);
      }
    } catch (e) {
      alert(e.response?.data?.detail || 'Error');
    }
    setActionModal(null);
    setReason('');
    load();
  };

  const openPdf = (url) => { if (url) window.open(url, '_blank'); };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100">Invoices</h1>
        <div className="flex gap-1 bg-zinc-800 rounded p-0.5">
          <button onClick={() => setView('list')} className={`text-[10px] px-2.5 py-1 rounded flex items-center gap-1 ${view === 'list' ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500'}`}>
            <List size={12} /> List
          </button>
          <button onClick={() => setView('kanban')} className={`text-[10px] px-2.5 py-1 rounded flex items-center gap-1 ${view === 'kanban' ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500'}`}>
            <Columns3 size={12} /> Kanban
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-3.5 flex-wrap items-center">
        <div className="relative max-w-[220px] flex-1">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
          <input
            placeholder="Search invoice, supplier, OC..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[11px] pl-8 pr-3 py-2 rounded focus:border-amber-500 outline-none"
          />
        </div>
        <span className="text-[9px] text-zinc-500 tracking-widest uppercase">Status:</span>
        {[null, 'PENDING', 'APPROVED', 'PAID', 'REJECTED'].map(s => (
          <button key={s || 'all'} onClick={() => setStatusFilter(s)} className={`text-[11px] px-3 py-1 rounded-full border transition-all ${statusFilter === s ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* LIST VIEW */}
      {view === 'list' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
          {filtered.map(inv => {
            const pill = PILL[inv.status] || PILL.PENDING;
            return (
              <div key={inv.id} className="flex items-center gap-2.5 px-3.5 py-2.5 border-b border-white/[.04] last:border-0 hover:bg-white/[.02] transition-colors">
                <div className="w-7 h-7 bg-red-400/[.08] rounded flex items-center justify-center border border-red-400/[.12] flex-shrink-0">
                  <svg className="w-3.5 h-3.5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-zinc-200 font-mono">{inv.invoice_number}</div>
                  <div className="text-[10px] text-zinc-500">{inv.supplier_name} &middot; {inv.oc_number}</div>
                </div>
                <div className="font-mono text-xs font-medium text-zinc-200 mx-2 hidden sm:block">{inv.final_total.toFixed(2)} EUR</div>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${pill.cls}`}>
                  <span className={`w-1 h-1 rounded-full ${pill.dot}`} />{inv.status}
                </span>
                {/* Actions */}
                <div className="flex gap-1 ml-1">
                  {inv.file_url && (
                    <button onClick={() => openPdf(inv.file_url)} title="View PDF" className="p-1 hover:bg-zinc-800 rounded transition-colors text-zinc-500 hover:text-zinc-300">
                      <ExternalLink size={13} />
                    </button>
                  )}
                  {inv.status === 'PENDING' && (
                    <>
                      <button onClick={() => setActionModal({ invoice: inv, action: 'approve' })} title="Approve" className="p-1 hover:bg-green-400/10 rounded transition-colors text-green-400">
                        <Check size={13} />
                      </button>
                      <button onClick={() => setActionModal({ invoice: inv, action: 'reject' })} title="Reject" className="p-1 hover:bg-red-400/10 rounded transition-colors text-red-400">
                        <X size={13} />
                      </button>
                    </>
                  )}
                  {inv.status === 'APPROVED' && (
                    <button onClick={() => setActionModal({ invoice: inv, action: 'pay' })} title="Mark as paid" className="p-1 hover:bg-green-300/10 rounded transition-colors text-green-300">
                      <CreditCard size={13} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center py-8 text-xs text-zinc-600">No invoices found</div>
          )}
        </div>
      )}

      {/* KANBAN VIEW */}
      {view === 'kanban' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {KANBAN_COLS.map(col => {
            const pill = PILL[col] || PILL.PENDING;
            const colInvoices = filtered.filter(i => i.status === col);
            return (
              <div key={col} className="bg-zinc-900 border border-zinc-800 rounded-md p-2.5">
                <div className="text-[9px] font-semibold text-zinc-400 mb-2 flex items-center gap-1.5 tracking-widest uppercase">
                  <span className={`w-1.5 h-1.5 rounded-full ${pill.dot}`} />
                  {col}
                  <span className="bg-zinc-800 text-zinc-400 text-[10px] px-1.5 rounded font-mono">{colInvoices.length}</span>
                </div>
                {colInvoices.map(inv => (
                  <div key={inv.id} className="bg-zinc-800 border border-zinc-700 rounded p-2.5 mb-1.5 cursor-pointer hover:border-amber-500 transition-colors">
                    <div className="text-[10px] text-zinc-500 font-mono flex items-center gap-1">
                      {inv.invoice_number}
                    </div>
                    <div className="text-xs font-medium text-zinc-200 mt-0.5">{inv.supplier_name}</div>
                    <div className="font-mono text-[13px] text-zinc-100 mt-0.5">{inv.final_total.toFixed(2)} EUR</div>
                    <div className="text-[10px] text-zinc-500 mt-1 pt-1 border-t border-zinc-700">
                      OC: <span className="text-amber-400">{inv.oc_number}</span>
                    </div>
                    {/* Inline actions */}
                    <div className="flex gap-1 mt-1.5">
                      {inv.file_url && (
                        <button onClick={() => openPdf(inv.file_url)} className="text-[9px] text-zinc-500 hover:text-zinc-300 border border-zinc-700 px-1.5 py-0.5 rounded">PDF</button>
                      )}
                      {col === 'PENDING' && (
                        <>
                          <button onClick={() => setActionModal({ invoice: inv, action: 'approve' })} className="text-[9px] text-green-400 border border-green-400/25 px-1.5 py-0.5 rounded hover:bg-green-400/10">Approve</button>
                          <button onClick={() => setActionModal({ invoice: inv, action: 'reject' })} className="text-[9px] text-red-400 border border-red-400/25 px-1.5 py-0.5 rounded hover:bg-red-400/10">Reject</button>
                        </>
                      )}
                      {col === 'APPROVED' && (
                        <button onClick={() => setActionModal({ invoice: inv, action: 'pay' })} className="text-[9px] text-green-300 border border-green-300/25 px-1.5 py-0.5 rounded hover:bg-green-300/10">Paid</button>
                      )}
                    </div>
                  </div>
                ))}
                {colInvoices.length === 0 && (
                  <div className="text-[10px] text-zinc-700 text-center py-4">Empty</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Action modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => { setActionModal(null); setReason(''); }}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">
              {actionModal.action === 'approve' && 'Approve invoice'}
              {actionModal.action === 'pay' && 'Mark as paid'}
              {actionModal.action === 'reject' && 'Reject invoice'}
              {actionModal.action === 'delete' && 'Confirm deletion'}
            </h3>
            <p className="text-xs text-zinc-500 mb-4">
              Invoice <span className="font-mono text-zinc-300">{actionModal.invoice.invoice_number}</span> from {actionModal.invoice.supplier_name}
              {actionModal.action !== 'reject' && ' — Are you sure?'}
            </p>
            {actionModal.action === 'reject' && (
              <div className="mb-4">
                <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Rejection reason <span className="text-amber-500">*</span></label>
                <textarea
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  rows={3}
                  placeholder="Explain why this invoice is being rejected..."
                  className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded focus:border-amber-500 outline-none resize-none"
                />
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setActionModal(null); setReason(''); }} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancel</button>
              <button
                onClick={handleAction}
                disabled={actionModal.action === 'reject' && !reason.trim()}
                className={`text-xs px-4 py-2 rounded font-semibold transition-colors disabled:opacity-40 ${
                  actionModal.action === 'reject' ? 'bg-red-500 hover:bg-red-400 text-white' :
                  'bg-amber-500 hover:bg-amber-400 text-zinc-950'
                }`}
              >
                {actionModal.action === 'approve' && 'Approve'}
                {actionModal.action === 'pay' && 'Confirm payment'}
                {actionModal.action === 'reject' && 'Reject'}
                {actionModal.action === 'delete' && 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoicesList;
