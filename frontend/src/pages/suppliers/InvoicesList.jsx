import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Trash2, X, CreditCard, Mic, Info, RotateCcw } from 'lucide-react';
import { getAllInvoices, updateInvoiceStatus, deleteInvoice, rejectInvoiceDeletion } from '../../services/suppliersApi';
import { getCompanies } from '../../services/api';
import { showError } from '../../utils/toast';
import useVoiceSearch from '../../hooks/useVoiceSearch';
import useEscapeKey from '../../hooks/useEscapeKey';
import useClickOutside from '../../hooks/useClickOutside';
import { INVOICE_PILL } from '../../constants/invoiceStatus';

const getPageNumbers = (current, total) => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i);
  const pages = new Set([0, total - 1]);
  for (let i = Math.max(1, current - 1); i <= Math.min(total - 2, current + 1); i++) pages.add(i);
  const sorted = [...pages].sort((a, b) => a - b);
  const result = [];
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) result.push('...');
    result.push(sorted[i]);
  }
  return result;
};

const PILL = INVOICE_PILL;

const PAGE_SIZE = 20;

const InvoicesList = () => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);
  const [actionModal, setActionModal] = useState(null);
  const [reason, setReason] = useState('');
  const [acting, setActing] = useState(false);
  const [page, setPage] = useState(0);
  const [totalLoaded, setTotalLoaded] = useState(0);

  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => { setSearch(transcript); setShowSuggestions(false); }, []),
  });
  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));
  useEscapeKey(() => { setActionModal(null); setReason(''); }, !!actionModal);

  const handleSearchChange = (value) => { setSearch(value); setShowSuggestions(value.length > 0); };
  const clearSearch = () => { setSearch(''); setShowSuggestions(false); };
  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches_invoices', JSON.stringify(updated));
  };

  const load = () => {
    const params = { limit: 200 };
    if (statusFilter) params.status = statusFilter;
    if (companyFilter) params.company_id = companyFilter;
    Promise.all([getAllInvoices(params), getCompanies()])
      .then(([inv, c]) => { setInvoices(inv.data); setTotalLoaded(inv.data.length); setCompanies(c.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { setLoading(true); setPage(0); load(); }, [statusFilter, companyFilter]);
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches_invoices');
    if (saved) setRecentSearches(JSON.parse(saved));
  }, []);

  const filtered = invoices.filter(inv => {
    if (!search) return true;
    const q = search.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) ||
      inv.supplier_name?.toLowerCase().includes(q) ||
      inv.oc_number?.toLowerCase().includes(q);
  });

  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  const handleAction = async () => {
    if (!actionModal || acting) return;
    setActing(true);
    const { invoice, action } = actionModal;
    try {
      if (action === 'approve') await updateInvoiceStatus(invoice.id, { status: 'APPROVED' });
      else if (action === 'pay') await updateInvoiceStatus(invoice.id, { status: 'PAID' });
      else if (action === 'delete') { if (!reason.trim()) { setActing(false); return; } await deleteInvoice(invoice.id, reason); }
      else if (action === 'confirm_delete') await deleteInvoice(invoice.id, null);
      else if (action === 'reject_delete') await rejectInvoiceDeletion(invoice.id);
    } catch (e) { showError(e.response?.data?.detail || 'Error'); }
    setActionModal(null); setReason(''); setActing(false); load();
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">Facturas</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-3.5 flex-wrap items-center">
        <div className="relative w-full sm:w-[300px]" ref={searchRef}>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-zinc-500 pointer-events-none" size={14} />
            <input
              type="text"
              placeholder="Buscar factura, OC, proveedor..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => (search || recentSearches.length > 0) && setShowSuggestions(true)}
              onKeyDown={(e) => { if (e.key === 'Enter' && search.trim()) { saveRecentSearch(search); setShowSuggestions(false); } }}
              className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[13px] pl-9 pr-14 py-2 rounded-sm focus:border-amber-500 outline-none"
            />
            <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
              {search && (
                <button onClick={clearSearch} className="p-1 hover:bg-zinc-800 rounded-sm transition-colors" title="Limpiar búsqueda">
                  <X size={14} className="text-zinc-500" />
                </button>
              )}
              <button onClick={startVoiceSearch} disabled={isListening}
                className={`p-1 rounded-sm transition-colors ${isListening ? 'bg-red-500 text-white animate-pulse' : 'hover:bg-zinc-800 text-zinc-500'}`}
                title="Búsqueda por voz">
                <Mic size={14} />
              </button>
            </div>
          </div>
          {showSuggestions && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded shadow-xl max-h-64 overflow-y-auto z-50">
              {search && (() => {
                const hits = invoices.filter(inv => {
                  const q = search.toLowerCase();
                  return inv.invoice_number?.toLowerCase().includes(q) || inv.supplier_name?.toLowerCase().includes(q) || inv.oc_number?.toLowerCase().includes(q);
                }).slice(0, 5);
                return hits.length > 0 ? (
                  <>
                    <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Facturas encontradas</div>
                    {hits.map(inv => (
                      <div key={inv.id} onClick={() => { setSearch(inv.invoice_number); saveRecentSearch(inv.invoice_number); setShowSuggestions(false); }}
                        className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-300 border-b border-zinc-800/50 last:border-0">
                        <span className="font-mono text-amber-400">{inv.invoice_number}</span>
                        {inv.supplier_name && <span className="text-zinc-500 ml-2">· {inv.supplier_name}</span>}
                      </div>
                    ))}
                  </>
                ) : <div className="px-3 py-3 text-xs text-zinc-600 text-center">Sin resultados</div>;
              })()}
              {!search && recentSearches.length > 0 && (
                <>
                  <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Búsquedas recientes</div>
                  {recentSearches.map((term, i) => (
                    <div key={i} onClick={() => { setSearch(term); setShowSuggestions(false); }}
                      className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-400 border-b border-zinc-800/50 last:border-0">
                      {term}
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
        <select value={companyFilter} onChange={e => setCompanyFilter(e.target.value)}
          className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-[13px] px-2.5 py-2 rounded outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}>
          <option value="">Todas las empresas</option>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-[13px] px-2.5 py-2 rounded outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}>
          <option value="">Todos los estados</option>
          <option value="PENDING">Pendiente</option>
          <option value="OC_PENDING">Sin OC</option>
          <option value="APPROVED">Aprobada</option>
          <option value="PAID">Pagada</option>
          <option value="DELETE_REQUESTED">Borrado solicitado</option>
        </select>
      </div>

      {/* Info banner for OC_PENDING filter */}
      {statusFilter === 'OC_PENDING' && filtered.length > 0 && (
        <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-2.5 text-[13px] mb-3 flex items-start gap-2">
          <Info size={14} className="flex-shrink-0 mt-0.5" />
          {filtered.length} factura(s) sin OC asignado — la IA no pudo identificar el proyecto. Haz clic en la factura para asignar OC manualmente.
        </div>
      )}

      {/* CARDS — solo móvil */}
      <div className="lg:hidden flex flex-col gap-2 mb-4">
        {paged.length === 0 ? (
          <div className="text-center py-8 text-xs text-zinc-600">Sin facturas</div>
        ) : paged.map(inv => {
          const pill = PILL[inv.status] || PILL.PENDING;
          return (
            <div key={inv.id} onClick={() => navigate(`/suppliers/invoices/${inv.id}?from=list`)}
              className={`bg-zinc-900 border rounded-md p-3.5 cursor-pointer active:border-amber-500 transition-colors ${inv.status === 'OC_PENDING' ? 'border-blue-400/20 bg-blue-400/[.02]' : 'border-zinc-800'}`}>
              <div className="flex items-start justify-between mb-2">
                <span className="font-mono text-[13px] text-zinc-200">{inv.invoice_number}
                  {inv.is_autoinvoice && <span className="ml-1.5 text-[8px] px-1.5 py-[1px] rounded bg-blue-400/10 text-blue-400 border border-blue-400/20 font-sans font-bold">AUTO</span>}
                  {inv.from_supplier_portal && !inv.is_autoinvoice && <span className="ml-1.5 text-[8px] px-1.5 py-[1px] rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-sans font-bold">PORTAL</span>}
                </span>
                <span className="font-mono text-[13px] font-semibold text-zinc-100">{inv.final_total?.toFixed(2)} €</span>
              </div>
              <div className="text-[12px] text-zinc-400 mb-2">{inv.supplier_name}</div>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  {inv.oc_number
                    ? <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{inv.oc_number}</span>
                    : <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-400/[.08] text-blue-400 border border-blue-400/15 font-semibold">Sin OC</span>
                  }
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${pill.cls}`}>
                    <span className={`w-1 h-1 rounded-full ${pill.dot}`} />{inv.status === 'OC_PENDING' ? 'Sin OC' : inv.status}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0" onClick={e => e.stopPropagation()}>
                  {inv.status === 'OC_PENDING' && (
                    <button onClick={(e) => { e.stopPropagation(); navigate(`/suppliers/invoices/${inv.id}?from=list`); }}
                      className="text-[12px] text-blue-400 border border-blue-400/30 px-2.5 py-1 rounded hover:bg-blue-400/10">Asignar OC →</button>
                  )}
                  {inv.status === 'PENDING' && (
                    <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'approve' }); }}
                      className="text-[12px] bg-amber-500 text-zinc-950 font-semibold px-2.5 py-1 rounded hover:bg-amber-400">Aprobar</button>
                  )}
                  {inv.status === 'APPROVED' && (
                    <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'pay' }); }}
                      className="text-[12px] text-zinc-400 border border-zinc-700 px-2.5 py-1 rounded hover:bg-zinc-800">Pagar</button>
                  )}
                  {inv.status === 'DELETE_REQUESTED' && (
                    <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'reject_delete' }); }}
                      className="w-[30px] h-[30px] flex items-center justify-center border border-amber-500/20 rounded text-amber-400/60 hover:text-amber-400 hover:bg-amber-400/10">
                      <RotateCcw size={13} strokeWidth={1.5} />
                    </button>
                  )}
                  {(inv.status === 'PENDING' || inv.status === 'OC_PENDING' || inv.status === 'DELETE_REQUESTED') && (
                    <button onClick={(e) => { e.stopPropagation(); if (inv.status === 'DELETE_REQUESTED') { setActionModal({ invoice: inv, action: 'confirm_delete' }); } else { setActionModal({ invoice: inv, action: 'delete' }); } }}
                      className="w-[30px] h-[30px] flex items-center justify-center border border-red-400/20 rounded text-red-400/60 hover:text-red-400 hover:bg-red-400/10">
                      <Trash2 size={13} strokeWidth={1.5} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* LIST VIEW — solo desktop */}
      <div className="hidden lg:block">
      <>
          <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-x-auto">
            <table className="w-full min-w-[650px]">
              <thead>
                <tr>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Nº Factura</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Proveedor</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Proyecto · OC</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Importe</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Estado</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium w-[140px]">Acción</th>
                  <th className="bg-zinc-800 px-3 py-2.5 w-9"></th>
                </tr>
              </thead>
              <tbody>
                {paged.map(inv => {
                  const pill = PILL[inv.status] || PILL.PENDING;
                  return (
                    <tr key={inv.id} onClick={() => navigate(`/suppliers/invoices/${inv.id}?from=list`)} className="hover:bg-white/[.02] transition-colors cursor-pointer">
                      <td className="px-3 py-2.5 border-b border-white/[.04] font-mono text-[13px] text-zinc-200">
                        {inv.invoice_number}
                        {inv.is_autoinvoice && <span className="ml-1.5 text-[8px] px-1.5 py-[1px] rounded bg-blue-400/10 text-blue-400 border border-blue-400/20 font-sans font-bold">AUTO</span>}
                        {inv.from_supplier_portal && !inv.is_autoinvoice && <span className="ml-1.5 text-[8px] px-1.5 py-[1px] rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-sans font-bold">PORTAL</span>}
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04] text-[13px] text-zinc-200">{inv.supplier_name}</td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        {inv.oc_number
                          ? <span className="text-[11px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{inv.oc_number}</span>
                          : <span className="text-[11px] px-1.5 py-[1px] rounded bg-blue-400/[.08] text-blue-400 border border-blue-400/15 font-semibold">Sin OC</span>
                        }
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04] font-mono text-[13px] text-zinc-200">{inv.final_total?.toFixed(2)} EUR</td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        <span className={`text-[12px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${pill.cls}`}>
                          <span className={`w-1 h-1 rounded-full ${pill.dot}`} />{inv.status}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        {inv.status === 'OC_PENDING' && (
                          <button onClick={(e) => { e.stopPropagation(); navigate(`/suppliers/invoices/${inv.id}?from=list`); }}
                            className="text-[13px] text-blue-400 border border-blue-400/30 px-2.5 py-1 rounded hover:bg-blue-400/10 transition-colors">Asignar OC →</button>
                        )}
                        {inv.status === 'PENDING' && (
                          <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'approve' }); }} className="text-[13px] bg-amber-500 text-zinc-950 font-semibold px-2.5 py-1 rounded transition-colors hover:bg-amber-400">Aprobar</button>
                        )}
                        {inv.status === 'APPROVED' && (
                          <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'pay' }); }} className="text-[13px] text-zinc-400 border border-zinc-700 px-2.5 py-1 rounded hover:bg-zinc-800 transition-colors">Marcar pagada</button>
                        )}
                        {inv.status === 'DELETE_REQUESTED' && (
                          <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'reject_delete' }); }}
                            className="text-[13px] text-amber-400 border border-amber-500/30 px-2.5 py-1 rounded hover:bg-amber-400/10 transition-colors">↩ Rechazar</button>
                        )}
                        {inv.status === 'PAID' && <span className="text-[13px] text-zinc-600">Cerrada</span>}
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        {(inv.status === 'PENDING' || inv.status === 'OC_PENDING' || inv.status === 'DELETE_REQUESTED') ? (
                          <button onClick={(e) => { e.stopPropagation(); if (inv.status === 'DELETE_REQUESTED') { setActionModal({ invoice: inv, action: 'confirm_delete' }); } else { setActionModal({ invoice: inv, action: 'delete' }); } }}
                            className="w-7 h-7 flex items-center justify-center border border-red-400/20 rounded text-red-400/60 hover:text-red-400 hover:bg-red-400/10 transition-colors">
                            <Trash2 size={12} strokeWidth={1.5} />
                          </button>
                        ) : (
                          <div className="w-7 h-7 flex items-center justify-center">
                            <Trash2 size={12} className="text-zinc-800" strokeWidth={1.5} />
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {paged.length === 0 && <tr><td colSpan="7" className="text-center py-8 text-xs text-zinc-600">Sin facturas</td></tr>}
              </tbody>
            </table>
          </div>
          {/* Pagination (I3) */}
          <div className="flex items-center justify-between mt-2 text-[13px] text-zinc-500">
            <span>Mostrando {Math.min(page * PAGE_SIZE + 1, filtered.length)}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} de {filtered.length} facturas</span>
            {totalPages > 1 && (
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="px-2.5 py-1 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">← Anterior</button>
                {getPageNumbers(page, totalPages).map((p, i) =>
                  p === '...' ? (
                    <span key={`e${i}`} className="px-1.5 py-1 text-zinc-600">…</span>
                  ) : (
                    <button key={p} onClick={() => setPage(p)} className={`px-2.5 py-1 rounded border transition-colors ${page === p ? 'bg-zinc-800 text-zinc-200 border-zinc-600' : 'border-zinc-700 text-zinc-500 hover:bg-zinc-800'}`}>{p + 1}</button>
                  )
                )}
                <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-2.5 py-1 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">Siguiente →</button>
              </div>
            )}
          </div>
        </>
      </div>

      {/* Action modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => { setActionModal(null); setReason(''); }}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">
              {actionModal.action === 'approve' && 'Aprobar factura'}
              {actionModal.action === 'pay' && 'Marcar como pagada'}
              {(actionModal.action === 'delete' || actionModal.action === 'confirm_delete') && 'Eliminar factura'}
              {actionModal.action === 'reject_delete' && 'Rechazar borrado'}
            </h3>
            <p className="text-xs text-zinc-500 mb-4">
              {actionModal.action === 'confirm_delete'
                ? '¿Confirmar borrado definitivo? El proveedor ya solicitó la eliminación.'
                : actionModal.action === 'reject_delete'
                ? '¿Rechazar la solicitud de borrado? La factura volverá a su estado anterior.'
                : <>Factura <span className="font-mono text-zinc-300">{actionModal.invoice.invoice_number}</span> de {actionModal.invoice.supplier_name}</>}
            </p>
            {actionModal.action === 'delete' && (
              <div className="mb-4">
                <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Motivo <span className="text-amber-500">*</span></label>
                <textarea value={reason} onChange={e => setReason(e.target.value)} rows={3} placeholder="Explica el motivo..." className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded focus:border-amber-500 outline-none resize-none" />
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setActionModal(null); setReason(''); }} disabled={acting} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors disabled:opacity-40">Cancelar</button>
              <button onClick={handleAction} disabled={acting || (actionModal.action === 'delete' && !reason.trim())}
                className={`text-xs px-4 py-2 rounded font-semibold transition-colors disabled:opacity-40 ${actionModal.action === 'delete' || actionModal.action === 'confirm_delete' ? 'bg-red-500 hover:bg-red-400 text-white' : 'bg-amber-500 hover:bg-amber-400 text-zinc-950'}`}>
                {actionModal.action === 'approve' ? 'Aprobar' : actionModal.action === 'pay' ? 'Confirmar pago' : actionModal.action === 'reject_delete' ? 'Rechazar borrado' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoicesList;
