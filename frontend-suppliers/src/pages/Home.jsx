import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSummary, getMyInvoices, getReceivedInvoices, requestDeleteInvoice } from '../services/api';
import { Search, Trash2, Upload, Info, Download, FileText, X, ChevronLeft, ChevronRight } from 'lucide-react';
import useEscapeKey from '../hooks/useEscapeKey';

const PILL = {
  PENDING:   { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500' },
  APPROVED:  { cls: 'bg-green-400/10 text-green-400 border-green-400/20', dot: 'bg-green-400' },
  PAID:      { cls: 'bg-green-300/10 text-green-300 border-green-300/20', dot: 'bg-green-300' },
  DELETE_REQUESTED: { cls: 'bg-red-300/10 text-red-300 border-red-300/20', dot: 'bg-red-300' },
  OC_PENDING: { cls: 'bg-blue-400/10 text-blue-400 border-blue-400/20', dot: 'bg-blue-400' },
};

const STATUS_LABEL = {
  PENDING: 'Pending', APPROVED: 'Approved', PAID: 'Paid',
  DELETE_REQUESTED: 'Delete requested', OC_PENDING: 'OC Pending',
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
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [viewer, setViewer] = useState(null);
  const [viewerPage, setViewerPage] = useState(0);

  const load = () => {
    setError('');
    const params = {};
    if (statusFilter) params.status = statusFilter;
    Promise.all([getSummary(), getMyInvoices(params)])
      .then(([s, i]) => { setSummary(s.data); setInvoices(i.data); })
      .catch(() => setError('Failed to load invoices'))
      .finally(() => setLoading(false));
  };

  useEscapeKey(() => { setDeleteModal(null); setReason(''); }, !!deleteModal);
  useEscapeKey(() => setViewer(null), !!viewer);

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
    if (!deleteModal || !reason.trim() || deleting) return;
    setDeleting(true);
    try { await requestDeleteInvoice(deleteModal.id, reason); } catch { setError('Failed to delete invoice'); }
    finally { setDeleting(false); }
    setDeleteModal(null); setReason(''); load();
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="relative max-w-2xl lg:max-w-4xl mx-auto pt-4 lg:pt-6 lg:px-6">
      {error && (
        <div className="mx-4 lg:mx-0 mb-3 bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-2.5 text-[12px]">{error}</div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-2 lg:gap-4 px-4 lg:px-0 mb-4 lg:mb-6">
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3 lg:p-6 border-l-2 border-l-amber-500">
          <div className="text-[11px] text-zinc-500 tracking-widest uppercase mb-1 lg:mb-2">Pending payment</div>
          <div className="font-['Bebas_Neue'] text-[30px] lg:text-[36px] text-amber-500 leading-none tracking-wide">
            {Math.round(summary?.pending_amount || 0).toLocaleString()}<span className="text-zinc-500 text-sm ml-0.5">EUR</span>
          </div>
          <div className="text-[11px] text-zinc-500 mt-0.5 lg:mt-1">
            {invoices.filter(i => i.status === 'PENDING' || i.status === 'APPROVED').length} invoice(s)
          </div>
        </div>
        <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3 lg:p-6">
          <div className="text-[11px] text-zinc-500 tracking-widest uppercase mb-1 lg:mb-2">Paid this month</div>
          <div className="font-['Bebas_Neue'] text-[30px] lg:text-[36px] text-green-400 leading-none tracking-wide">
            {Math.round(summary?.paid_this_month || 0).toLocaleString()}<span className="text-zinc-500 text-sm ml-0.5">EUR</span>
          </div>
          <div className="text-[11px] text-zinc-500 mt-0.5 lg:mt-1">{summary?.total_invoices || 0} total</div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-zinc-800 mx-4 lg:mx-0 mb-3.5">
        <button onClick={() => setActiveTab('mine')}
          className={`flex-1 py-2.5 lg:py-3.5 text-center text-[12px] lg:text-[14px] border-b-2 transition-colors ${activeTab === 'mine' ? 'text-amber-400 border-amber-500 font-semibold' : 'text-zinc-500 border-transparent'}`}>
          All invoices ({invoices.length})
        </button>
        <button onClick={() => setActiveTab('received')}
          className={`flex-1 py-2.5 lg:py-3.5 text-center text-[12px] lg:text-[14px] border-b-2 transition-colors ${activeTab === 'received' ? 'text-amber-400 border-amber-500 font-semibold' : 'text-zinc-500 border-transparent'}`}>
          Received{receivedInvoices.length > 0 ? ` (${receivedInvoices.length})` : ''}
        </button>
      </div>

      {/* ═══ TAB: All invoices ═══ */}
      {activeTab === 'mine' && (
        <>
          {/* Filters — móvil: apilado, desktop: en línea */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-2 lg:gap-3 px-4 lg:px-0 mb-3">
            <span className="text-[11px] font-semibold text-zinc-400 tracking-widest uppercase lg:shrink-0">Invoices</span>
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" strokeWidth={1.5} />
              <input
                placeholder="Search invoice or OC..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-[#27272a] border border-zinc-700 text-zinc-100 text-xs pl-9 pr-3 py-2.5 rounded-[10px] focus:border-amber-500 outline-none placeholder:text-zinc-600"
              />
            </div>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="bg-[#27272a] border border-zinc-700 rounded-lg px-2.5 py-1.5 text-[11px] text-zinc-300 outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center] lg:w-40"
              style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}
            >
              <option value="">All</option>
              <option value="PENDING">Pending</option>
              <option value="OC_PENDING">OC Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="PAID">Paid</option>
              <option value="DELETE_REQUESTED">Delete requested</option>
            </select>
          </div>

          {/* Invoice cards */}
          <div className="px-4 lg:px-0 space-y-2 lg:space-y-3 mb-3">
            {filtered.length === 0 ? (
              error ? (
                <div className="text-center py-12">
                  <p className="text-xs text-red-400 mb-3">Error loading invoices. Please try again.</p>
                  <button onClick={() => { setLoading(true); load(); }}
                    className="text-[12px] bg-zinc-800 border border-zinc-700 text-zinc-300 px-4 py-2 rounded-lg hover:bg-zinc-700 transition-colors">
                    Retry
                  </button>
                </div>
              ) : (
                <div className="text-center py-12 text-xs text-zinc-600">No invoices</div>
              )
            ) : filtered.map(inv => {
              const pill = PILL[inv.status] || PILL.PENDING;
              return (
                <div key={inv.id} onClick={() => inv.file_url && setViewer(inv)}
                  className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 lg:p-5 transition-colors active:border-amber-500/50 hover:border-zinc-700 cursor-pointer">
                  <div className="flex items-start justify-between mb-2 lg:mb-3">
                    <span className="font-['IBM_Plex_Mono'] text-xs lg:text-sm font-medium text-zinc-200">{inv.invoice_number}</span>
                    <span className="font-['IBM_Plex_Mono'] text-sm lg:text-base font-semibold text-zinc-100">
                      {inv.final_total?.toLocaleString('en', { minimumFractionDigits: 2 })} EUR
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-[10px] lg:text-[11px] text-zinc-500 mb-1.5 flex items-center gap-1.5 flex-wrap">
                        {inv.oc_number && (
                          <span className="text-[9px] lg:text-[10px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-semibold font-['IBM_Plex_Mono'] border border-amber-500/15">
                            {inv.oc_number}
                          </span>
                        )}
                        {inv.date}
                      </div>
                      <span className={`text-[10px] lg:text-[11px] font-medium px-2 py-[3px] rounded-full border inline-flex items-center gap-1 ${pill.cls}`}>
                        <span className={`w-[5px] h-[5px] rounded-full ${pill.dot}`} />{STATUS_LABEL[inv.status] || inv.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {(inv.status === 'PENDING' || inv.status === 'OC_PENDING' || inv.status === 'APPROVED') ? (
                        <button onClick={(e) => { e.stopPropagation(); setDeleteModal(inv); }}
                          className="w-7 h-7 lg:w-8 lg:h-8 border border-red-400/20 rounded-md flex items-center justify-center text-red-400 hover:bg-red-400/10 transition-colors">
                          <Trash2 size={13} strokeWidth={1.5} />
                        </button>
                      ) : (
                        <div className="w-7 h-7 lg:w-8 lg:h-8 flex items-center justify-center">
                          <Trash2 size={13} className="text-zinc-800" strokeWidth={1.5} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <p className="px-4 lg:px-0 text-[10px] text-zinc-600 mb-20 lg:mb-8">
            Paid invoices cannot be deleted — they are already in accounting.
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
        <div className="px-4 lg:px-0">
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
            <div className="space-y-2 lg:space-y-3">
              {receivedInvoices.map(inv => (
                <div key={inv.id} onClick={() => inv.file_url && setViewer(inv)}
                  className="bg-[#18181b] border border-blue-400/15 bg-blue-400/[.02] rounded-[10px] p-3.5 lg:p-5 cursor-pointer hover:border-blue-400/30 transition-colors">
                  <div className="text-[10px] text-blue-400 tracking-widest uppercase mb-1.5 flex items-center gap-1">
                    <FileText size={10} strokeWidth={2} /> Generated by DAZZ
                  </div>
                  <div className="flex items-start justify-between mb-2 lg:mb-3">
                    <span className="font-['IBM_Plex_Mono'] text-xs lg:text-sm font-medium text-zinc-200">{inv.invoice_number}</span>
                    <span className="font-['IBM_Plex_Mono'] text-sm lg:text-base font-semibold text-zinc-100">
                      {inv.final_total?.toLocaleString('en', { minimumFractionDigits: 2 })} EUR
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <div>
                      {inv.oc_number && (
                        <span className="text-[9px] lg:text-[10px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-['IBM_Plex_Mono'] border border-amber-500/15 mr-1.5">
                          {inv.oc_number}
                        </span>
                      )}
                      <span className="text-[11px] text-zinc-500">{inv.date}{inv.company_name ? ` · ${inv.company_name}` : ''}</span>
                      <div className="mt-1.5">
                        <span className="text-[10px] lg:text-[11px] font-medium px-2 py-[3px] rounded-full border inline-flex items-center gap-1 bg-blue-400/10 text-blue-400 border-blue-400/20">
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
                        setTimeout(() => URL.revokeObjectURL(a.href), 10000);
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
            <button onClick={handleDelete} disabled={!reason.trim() || deleting} className="w-full py-3 rounded-[10px] text-sm font-bold bg-red-400/15 text-red-400 border border-red-400/30 disabled:opacity-40 mb-2">
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
            <button onClick={() => { setDeleteModal(null); setReason(''); }} className="w-full py-2.5 rounded-[10px] text-xs bg-[#27272a] border border-zinc-700 text-zinc-300 text-center">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* ═══ Invoice Viewer Lightbox ═══ */}
      {viewer && (() => {
        const viewerIdx = filtered.findIndex(i => i.id === viewer.id);
        let pages = [];
        if (viewer.file_pages) {
          if (Array.isArray(viewer.file_pages)) pages = viewer.file_pages;
          else if (typeof viewer.file_pages === 'string') {
            try { const p = JSON.parse(viewer.file_pages); if (Array.isArray(p)) pages = p; } catch { /* ignore */ }
          }
        }
        const hasPages = pages.length > 0;
        const switchViewer = (inv) => { setViewerPage(0); setViewer(inv); };
        return (
          <div className="fixed inset-0 bg-zinc-950 z-[60] flex flex-col"
            style={{ minHeight: '100dvh', paddingTop: 'env(safe-area-inset-top, 0px)' }}>
            <div className="relative flex items-center justify-center px-6 py-4 border-b border-zinc-800">
              <div className="flex flex-col items-center gap-1">
                <div className="flex items-center gap-3">
                  {filtered.length > 1 && (
                    <button onClick={() => switchViewer(filtered[viewerIdx - 1])} disabled={viewerIdx <= 0}
                      className="text-[13px] px-3 py-1.5 border border-zinc-700 rounded text-zinc-300 hover:bg-zinc-800 disabled:opacity-30 transition-colors">
                      <span className="lg:hidden">←</span>
                      <span className="hidden lg:inline">← Previous</span>
                    </button>
                  )}
                  <span className="text-sm text-zinc-200 font-mono">{viewer.invoice_number}</span>
                  {filtered.length > 1 && (
                    <button onClick={() => switchViewer(filtered[viewerIdx + 1])} disabled={viewerIdx >= filtered.length - 1}
                      className="text-[13px] px-3 py-1.5 border border-zinc-700 rounded text-zinc-300 hover:bg-zinc-800 disabled:opacity-30 transition-colors">
                      <span className="lg:hidden">→</span>
                      <span className="hidden lg:inline">Next →</span>
                    </button>
                  )}
                </div>
                {filtered.length > 1 && (
                  <span className="text-[11px] text-zinc-500">{viewerIdx + 1}/{filtered.length}</span>
                )}
              </div>
              <button onClick={() => setViewer(null)}
                className="absolute top-4 right-4 text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 min-h-0 flex items-center justify-center overflow-hidden bg-zinc-950">
              {hasPages ? (
                <div className="relative w-full h-full flex items-center justify-center px-2">
                  {pages.length > 1 && viewerPage > 0 && (
                    <button onClick={() => setViewerPage(p => p - 1)}
                      className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center z-10">
                      <ChevronLeft size={28} /></button>
                  )}
                  <img src={pages[viewerPage]} alt={`Page ${viewerPage + 1}`}
                    className="max-w-full max-h-[80vh] object-contain select-none" />
                  {pages.length > 1 && viewerPage < pages.length - 1 && (
                    <button onClick={() => setViewerPage(p => p + 1)}
                      className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center z-10">
                      <ChevronRight size={28} /></button>
                  )}
                  {pages.length > 1 && (
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-zinc-900/80 px-4 py-2 rounded-full text-sm font-mono text-zinc-300 border border-zinc-700">
                      Page {viewerPage + 1} / {pages.length}
                    </div>
                  )}
                </div>
              ) : viewer.file_url ? (
                <iframe src={viewer.file_url} className="w-full h-full bg-white" title="Invoice PDF" />
              ) : (
                <p className="text-zinc-500 text-sm">No file available</p>
              )}
            </div>
            <div className="bg-zinc-900 border-t border-zinc-800 px-6 py-4 pb-[calc(1rem+env(safe-area-inset-bottom))] lg:pb-4 space-y-3 text-center">
              <div className="flex items-center justify-center gap-4">
                <span className="font-mono text-[13px] text-zinc-400">{viewer.invoice_number}</span>
                <span className="text-[18px] font-semibold text-zinc-100 font-mono">{viewer.final_total?.toLocaleString('en', { minimumFractionDigits: 2 })} EUR</span>
              </div>
              <div className="flex items-center justify-center flex-wrap gap-3">
                <span className={`text-[11px] font-medium px-2 py-[3px] rounded-full border inline-flex items-center gap-1.5 ${(PILL[viewer.status] || PILL.PENDING).cls}`}>
                  <span className={`w-[5px] h-[5px] rounded-full ${(PILL[viewer.status] || PILL.PENDING).dot}`} />
                  {STATUS_LABEL[viewer.status] || viewer.status}
                </span>
                <span className="text-[12px] text-zinc-500">{viewer.date}</span>
                {viewer.oc_number ? (
                  <span className="text-[11px] px-2 py-[2px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{viewer.oc_number}</span>
                ) : (
                  <span className="text-[11px] text-zinc-600">Pending assignment</span>
                )}
                {viewer.file_url && (
                  <a href={viewer.file_url} target="_blank" rel="noopener noreferrer"
                    className="text-[12px] text-zinc-300 border border-zinc-700 px-3 py-1.5 rounded hover:bg-zinc-800 transition-colors flex items-center gap-1.5">
                    <Download size={12} /> Download PDF
                  </a>
                )}
                {(viewer.status === 'PENDING' || viewer.status === 'OC_PENDING' || viewer.status === 'APPROVED') && (
                  <button onClick={() => { setViewer(null); setDeleteModal(viewer); }}
                    className="text-[12px] text-red-400 border border-red-400/25 px-3 py-1.5 rounded hover:bg-red-400/10 transition-colors flex items-center gap-1.5">
                    <Trash2 size={12} /> Delete
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default Home;
