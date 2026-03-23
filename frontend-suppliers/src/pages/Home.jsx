import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSummary, getMyInvoices, getReceivedInvoices, requestDeleteInvoice } from '../services/api';
import { Search, Trash2, ExternalLink, Upload, Info, Download, FileText } from 'lucide-react';
import useEscapeKey from '../hooks/useEscapeKey';

const PILL = {
  PENDING:   { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500' },
  APPROVED:  { cls: 'bg-green-400/10 text-green-400 border-green-400/20', dot: 'bg-green-400' },
  PAID:      { cls: 'bg-green-300/10 text-green-300 border-green-300/20', dot: 'bg-green-300' },
  REJECTED:  { cls: 'bg-red-400/10 text-red-400 border-red-400/20',     dot: 'bg-red-400' },
  DELETE_REQUESTED: { cls: 'bg-red-300/10 text-red-300 border-red-300/20', dot: 'bg-red-300' },
  OC_PENDING: { cls: 'bg-zinc-700/50 text-zinc-400 border-zinc-700',     dot: 'bg-zinc-500' },
};

const Home = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteModal, setDeleteModal] = useState(null);
  const [reason, setReason] = useState('');
  const [activeTab, setActiveTab] = useState('mine');
  const [receivedInvoices, setReceivedInvoices] = useState([]);
  const [receivedLoading, setReceivedLoading] = useState(false);

  const load = () => {
    const params = {};
    if (statusFilter) params.status = statusFilter;
    Promise.all([getSummary(), getMyInvoices(params)])
      .then(([s, i]) => { setSummary(s.data); setInvoices(i.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEscapeKey(() => { setDeleteModal(null); setReason(''); }, !!deleteModal);

  useEffect(() => { setLoading(true); load(); }, [statusFilter]);

  useEffect(() => {
    if (activeTab === 'received' && receivedInvoices.length === 0) {
      setReceivedLoading(true);
      getReceivedInvoices().then(r => setReceivedInvoices(r.data || [])).catch(() => {}).finally(() => setReceivedLoading(false));
    }
  }, [activeTab]);

  const filtered = invoices.filter(inv => {
    if (!search) return true;
    const q = search.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) || inv.oc_number?.toLowerCase().includes(q);
  });

  const handleDelete = async () => {
    if (!deleteModal || !reason.trim()) return;
    try { await requestDeleteInvoice(deleteModal.id, reason); } catch { /* handled below */ }
    setDeleteModal(null); setReason(''); load();
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="relative max-w-2xl mx-auto">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-2 px-4 mb-4">
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3 border-l-2 border-l-amber-500">
          <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-1">Pending payment</div>
          <div className="font-['Bebas_Neue'] text-[24px] text-amber-500 leading-none tracking-wide">
            {Math.round(summary?.pending_amount || 0).toLocaleString()}<span className="text-zinc-500 text-sm ml-0.5">EUR</span>
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">
            {invoices.filter(i => i.status === 'PENDING' || i.status === 'APPROVED').length} invoice(s)
          </div>
        </div>
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3">
          <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-1">Paid this month</div>
          <div className="font-['Bebas_Neue'] text-[24px] text-green-400 leading-none tracking-wide">
            {Math.round(summary?.paid_this_month || 0).toLocaleString()}<span className="text-zinc-500 text-sm ml-0.5">EUR</span>
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5">{summary?.total_invoices || 0} total</div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-zinc-800 mx-4 mb-3.5">
        <button onClick={() => setActiveTab('mine')}
          className={`flex-1 py-2.5 text-center text-[12px] border-b-2 transition-colors ${activeTab === 'mine' ? 'text-amber-400 border-amber-500 font-semibold' : 'text-zinc-500 border-transparent'}`}>
          My invoices ({invoices.length})
        </button>
        <button onClick={() => setActiveTab('received')}
          className={`flex-1 py-2.5 text-center text-[12px] border-b-2 transition-colors ${activeTab === 'received' ? 'text-amber-400 border-amber-500 font-semibold' : 'text-zinc-500 border-transparent'}`}>
          Received{receivedInvoices.length > 0 ? ` (${receivedInvoices.length})` : ''}
        </button>
      </div>

      {/* ═══ TAB: My invoices ═══ */}
      {activeTab === 'mine' && (
        <>
          {/* Filters */}
          <div className="flex items-center justify-between px-4 mb-2">
            <span className="text-[11px] font-semibold text-zinc-400 tracking-widest uppercase">Invoices</span>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="bg-[#27272a] border border-zinc-700 rounded-lg px-2.5 py-1.5 text-[11px] text-zinc-300 outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center]"
              style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}
            >
              <option value="">All</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="PAID">Paid</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          {/* Search */}
          <div className="mx-4 mb-3 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" strokeWidth={1.5} />
            <input
              placeholder="Search invoice or OC..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[#27272a] border border-zinc-700 text-zinc-100 text-xs pl-9 pr-3 py-2.5 rounded-[10px] focus:border-amber-500 outline-none placeholder:text-zinc-600"
            />
          </div>

          {/* Invoice cards */}
          <div className="px-4 space-y-2 mb-3">
            {filtered.length === 0 ? (
              <div className="text-center py-12 text-xs text-zinc-600">No invoices</div>
            ) : filtered.map(inv => {
              const pill = PILL[inv.status] || PILL.PENDING;
              return (
                <div key={inv.id} className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 transition-colors active:border-amber-500/50">
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-['IBM_Plex_Mono'] text-xs font-medium text-zinc-200">{inv.invoice_number}</span>
                    <span className="font-['IBM_Plex_Mono'] text-sm font-semibold text-zinc-100">
                      {inv.final_total?.toLocaleString('en', { minimumFractionDigits: 2 })} EUR
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-[10px] text-zinc-500 mb-1.5 flex items-center gap-1.5 flex-wrap">
                        {inv.oc_number && (
                          <span className="text-[9px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-semibold font-['IBM_Plex_Mono'] border border-amber-500/15">
                            {inv.oc_number}
                          </span>
                        )}
                        {inv.date}
                      </div>
                      <span className={`text-[10px] font-medium px-2 py-[3px] rounded-full border inline-flex items-center gap-1 ${pill.cls}`}>
                        <span className={`w-[5px] h-[5px] rounded-full ${pill.dot}`} />{inv.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {inv.file_url && (
                        <button onClick={() => window.open(inv.file_url, '_blank')} className="text-zinc-600 hover:text-zinc-300 transition-colors">
                          <ExternalLink size={15} strokeWidth={1.5} />
                        </button>
                      )}
                      {inv.status === 'PENDING' ? (
                        <button onClick={() => setDeleteModal(inv)} className="w-7 h-7 border border-red-400/20 rounded-md flex items-center justify-center text-red-400 hover:bg-red-400/10 transition-colors">
                          <Trash2 size={13} strokeWidth={1.5} />
                        </button>
                      ) : (
                        <div className="w-7 h-7 flex items-center justify-center">
                          <Trash2 size={13} className="text-zinc-800" strokeWidth={1.5} />
                        </div>
                      )}
                    </div>
                  </div>
                  {inv.rejection_reason && (
                    <div className="mt-2 text-[10px] text-red-400 bg-red-400/[.06] border border-red-400/[.12] rounded-lg p-2">
                      Rejected: {inv.rejection_reason}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <p className="px-4 text-[10px] text-zinc-600 mb-20">
            Approved and paid invoices cannot be deleted — they are already in accounting.
          </p>

          {/* FAB */}
          <button
            onClick={() => navigate('/upload')}
            className="fixed bottom-[80px] lg:bottom-6 right-4 w-[52px] h-[52px] bg-amber-500 rounded-full flex items-center justify-center shadow-lg shadow-amber-500/40 z-40 active:scale-95 transition-transform"
          >
            <Upload size={22} className="text-zinc-950" strokeWidth={2} />
          </button>
        </>
      )}

      {/* ═══ TAB: Received invoices ═══ */}
      {activeTab === 'received' && (
        <div className="px-4">
          <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded-lg p-3 text-[12px] flex items-start gap-2 mb-4">
            <Info size={14} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
            These invoices were generated by DAZZ on your behalf. They have been sent to your email.
          </div>

          {receivedLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : receivedInvoices.length === 0 ? (
            <div className="text-center py-16">
              <FileText size={40} className="text-zinc-700 mx-auto mb-2" strokeWidth={1} />
              <p className="text-[13px] text-zinc-500">No received invoices yet</p>
              <p className="text-[11px] text-zinc-600 mt-1">Invoices generated by DAZZ will appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {receivedInvoices.map(inv => (
                <div key={inv.id} className="bg-[#18181b] border border-blue-400/15 bg-blue-400/[.02] rounded-[10px] p-3.5">
                  <div className="text-[10px] text-blue-400 tracking-widest uppercase mb-1.5 flex items-center gap-1">
                    <FileText size={10} strokeWidth={2} /> Generated by DAZZ
                  </div>
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-['IBM_Plex_Mono'] text-xs font-medium text-zinc-200">{inv.invoice_number}</span>
                    <span className="font-['IBM_Plex_Mono'] text-sm font-semibold text-zinc-100">
                      {inv.final_total?.toLocaleString('en', { minimumFractionDigits: 2 })} EUR
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <div>
                      {inv.oc_number && (
                        <span className="text-[9px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-['IBM_Plex_Mono'] border border-amber-500/15 mr-1.5">
                          {inv.oc_number}
                        </span>
                      )}
                      <span className="text-[11px] text-zinc-500">{inv.date}{inv.company_name ? ` · ${inv.company_name}` : ''}</span>
                      <div className="mt-1.5">
                        <span className="text-[10px] font-medium px-2 py-[3px] rounded-full border inline-flex items-center gap-1 bg-blue-400/10 text-blue-400 border-blue-400/20">
                          <span className="w-[5px] h-[5px] rounded-full bg-blue-400" />Received
                        </span>
                      </div>
                    </div>
                    {inv.file_url && (
                      <button onClick={async () => {
                        const res = await fetch(inv.file_url);
                        const blob = await res.blob();
                        const a = document.createElement('a');
                        a.href = URL.createObjectURL(blob);
                        a.download = `${inv.invoice_number}.pdf`;
                        document.body.appendChild(a); a.click(); a.remove();
                        URL.revokeObjectURL(a.href);
                      }} className="text-[12px] bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-1.5 rounded-lg hover:bg-zinc-700 transition-colors flex items-center gap-1.5">
                        <Download size={12} strokeWidth={1.5} /> Download PDF
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Delete modal */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/70 z-[95] flex items-end sm:items-center sm:justify-center" onClick={() => { setDeleteModal(null); setReason(''); }}>
          <div className="bg-[#18181b] rounded-t-[20px] sm:rounded-[12px] p-5 pb-8 w-full sm:max-w-sm border-t border-zinc-800 sm:border" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-1">Delete invoice</h3>
            <p className="text-xs text-zinc-500 mb-4">The admin will receive a notification with your reason.</p>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              placeholder="e.g. Duplicate invoice, upload error..."
              className="w-full bg-[#27272a] border border-zinc-700 text-zinc-100 text-[13px] p-3 rounded-[10px] focus:border-amber-500 outline-none resize-none mb-3"
            />
            <button onClick={handleDelete} disabled={!reason.trim()} className="w-full py-3 rounded-[10px] text-sm font-bold bg-red-400/15 text-red-400 border border-red-400/30 disabled:opacity-40 mb-2">
              Delete
            </button>
            <button onClick={() => { setDeleteModal(null); setReason(''); }} className="w-full py-2.5 rounded-[10px] text-xs bg-[#27272a] border border-zinc-700 text-zinc-300 text-center">
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
