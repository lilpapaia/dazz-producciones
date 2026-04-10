import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Check, AlertTriangle, ExternalLink, X, ZoomIn, Download, Search, Trash2, RotateCcw } from 'lucide-react';
import { getInvoice, getAllInvoices, updateInvoiceStatus, assignInvoiceOC, getOCSuggestions, deleteInvoice, rejectInvoiceDeletion } from '../../services/suppliersApi';
import { showError, showSuccess } from '../../utils/toast';
import useEscapeKey from '../../hooks/useEscapeKey';
import { INVOICE_PILL, INVOICE_LABEL } from '../../constants/invoiceStatus';

const PILL = Object.fromEntries(Object.entries(INVOICE_PILL).map(([k, v]) => [k, v.cls]));
const PILL_LABEL = INVOICE_LABEL;

const InvoiceDetail = () => {
  const { invoiceId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const from = searchParams.get('from');
  const supplierId = searchParams.get('supplierId');

  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteModal, setDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [acting, setActing] = useState(false);
  const [confirmDeleteRequested, setConfirmDeleteRequested] = useState(false);

  // OC assignment
  const [ocSearch, setOcSearch] = useState('');
  const [ocSuggestions, setOcSuggestions] = useState([]);
  const [assigning, setAssigning] = useState(false);

  // Lightbox (ReviewTicket pattern)
  const [currentPage, setCurrentPage] = useState(0);
  const [showLightbox, setShowLightbox] = useState(false);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  // Navigation between invoices
  const [allIds, setAllIds] = useState([]);
  const currentIdx = allIds.indexOf(parseInt(invoiceId));

  const queryString = from === 'supplier' && supplierId ? `?from=supplier&supplierId=${supplierId}` : from === 'list' ? '?from=list' : '';

  useEscapeKey(() => setShowLightbox(false), showLightbox);
  useEscapeKey(() => { setDeleteModal(false); setDeleteReason(''); }, deleteModal);
  useEscapeKey(() => setConfirmDeleteRequested(false), confirmDeleteRequested);

  const load = () => {
    getInvoice(invoiceId)
      .then(r => setInvoice(r.data))
      .catch(() => { showError('Error al cargar factura'); navigate(-1); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { setCurrentPage(0); load(); }, [invoiceId]);

  // Load sibling invoice IDs for navigation
  useEffect(() => {
    const params = { limit: 200 };
    if (from === 'supplier' && supplierId) params.supplier_id = supplierId;
    getAllInvoices(params).then(r => {
      setAllIds((r.data || []).map(inv => inv.id));
    }).catch(() => {});
  }, [from, supplierId]);

  const goToPrev = () => {
    if (currentIdx > 0) navigate(`/suppliers/invoices/${allIds[currentIdx - 1]}${queryString}`);
  };
  const goToNext = () => {
    if (currentIdx >= 0 && currentIdx < allIds.length - 1) navigate(`/suppliers/invoices/${allIds[currentIdx + 1]}${queryString}`);
  };

  // Block scroll when lightbox open (ReviewTicket pattern)
  useEffect(() => {
    document.body.style.overflow = showLightbox ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [showLightbox]);

  // OC autocomplete with debounce
  useEffect(() => {
    if (ocSearch.length < 2) { setOcSuggestions([]); return; }
    const timer = setTimeout(() => {
      getOCSuggestions(ocSearch).then(r => setOcSuggestions(r.data)).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [ocSearch]);

  const handleAssignOC = async (ocNumber) => {
    setAssigning(true);
    try {
      await assignInvoiceOC(invoiceId, ocNumber);
      showSuccess(`OC "${ocNumber}" asignado`);
      setOcSearch('');
      setOcSuggestions([]);
      load();
    } catch (e) { showError(e.response?.data?.detail || 'Error al asignar OC'); }
    setAssigning(false);
  };

  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const handleTouchEnd = (e) => {
    touchEndX.current = e.changedTouches[0].clientX;
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 50) {
      if (diff > 0 && currentPage < pages.length - 1) setCurrentPage(p => p + 1);
      else if (diff < 0 && currentPage > 0) setCurrentPage(p => p - 1);
    }
  };

  const handleAction = async (status) => {
    setActing(true);
    try {
      await updateInvoiceStatus(invoiceId, { status });
      load();
    } catch (e) { showError(e.response?.data?.detail || 'Error'); }
    setActing(false);
  };

  const handleDelete = async (reason) => {
    setActing(true);
    try {
      await deleteInvoice(invoiceId, reason || null);
      showSuccess('Factura eliminada');
      navigate(from === 'supplier' && supplierId ? `/suppliers/${supplierId}` : '/suppliers/invoices');
    } catch (e) { showError(e.response?.data?.detail || 'Error'); }
    setDeleteModal(false);
    setDeleteReason('');
    setActing(false);
  };

  const handleRejectDeletion = async () => {
    setActing(true);
    try {
      await rejectInvoiceDeletion(invoiceId);
      showSuccess('Solicitud de borrado rechazada');
      load();
    } catch (e) { showError(e.response?.data?.detail || 'Error'); }
    setActing(false);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!invoice) return (
    <div className="text-center py-12">
      <p className="text-zinc-500 text-sm mb-3">Factura no encontrada</p>
      <button onClick={() => navigate('/suppliers/invoices')}
        className="text-amber-500 hover:text-amber-400 text-sm">← Volver a facturas</button>
    </div>
  );

  // Parse file_pages (ReviewTicket pattern)
  let pages = [];
  if (invoice.file_pages) {
    if (Array.isArray(invoice.file_pages)) pages = invoice.file_pages;
    else if (typeof invoice.file_pages === 'string') {
      try { const parsed = JSON.parse(invoice.file_pages); if (Array.isArray(parsed)) pages = parsed; } catch { /* ignore */ }
    }
  }
  const totalPages = pages.length;

  // Parse IA validation result
  let iaResult = null;
  if (invoice.ia_validation_result) {
    try { iaResult = JSON.parse(invoice.ia_validation_result); } catch { /* ignore */ }
  }

  const rowCls = "flex justify-between py-2 border-b border-white/[.04] last:border-0 text-xs";
  const labelCls = "text-zinc-500";
  const valCls = "text-zinc-200 text-right max-w-[200px] break-all";
  const monoCls = "font-mono text-[11px]";


  return (
    <div>
      {/* Header: breadcrumb | nav | status */}
      <div className="flex flex-col gap-3 mb-4">
        {/* Row 1: breadcrumb */}
        <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">
          <span onClick={() => navigate(from === 'supplier' && supplierId ? `/suppliers/${supplierId}` : '/suppliers/invoices')} className="text-zinc-500 cursor-pointer hover:text-amber-400 transition-colors">
            {from === 'supplier'
              ? (() => {
                  const name = (invoice.supplier_name || 'PROVEEDOR').toUpperCase();
                  const parts = name.trim().split(/\s+/);
                  return parts.length > 2 ? `${parts[0]} ${parts[1]}` : name;
                })()
              : 'FACTURAS'}
          </span>
          {' / '}{invoice.invoice_number}
        </h1>

        {/* Row 2: navigation + download + status */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Navigation */}
          {allIds.length > 1 && currentIdx >= 0 && (
            <div className="flex items-center gap-1.5">
              <button onClick={goToPrev} disabled={currentIdx <= 0}
                className="flex items-center gap-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-2.5 min-h-[44px] rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-xs">
                <ChevronLeft size={20} /> Anterior
              </button>
              <span className="font-mono text-sm text-amber-400 px-3 min-w-[50px] text-center">
                {currentIdx + 1} / {allIds.length}
              </span>
              <button onClick={goToNext} disabled={currentIdx >= allIds.length - 1}
                className="flex items-center gap-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-2.5 min-h-[44px] rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-xs">
                Siguiente <ChevronRight size={20} />
              </button>
            </div>
          )}

          {/* Download + status pill — always right */}
          <div className="flex items-center gap-2 ml-auto">
            {invoice.file_url && (
              <button onClick={async () => {
                try {
                  const res = await fetch(invoice.file_url);
                  const blob = await res.blob();
                  const a = document.createElement('a');
                  a.href = URL.createObjectURL(blob);
                  const supplier = (invoice.supplier_name || invoice.provider_name || 'proveedor').replace(/\s+/g, '_');
                  const date = invoice.date || '';
                  a.download = invoice.invoice_number
                    ? `${supplier}_${date}_${invoice.invoice_number}.pdf`
                    : `${supplier}_${date}.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
                } catch { showError('Error al descargar PDF'); }
              }}
                className="text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2.5 py-1.5 rounded border border-zinc-700 transition-colors flex items-center gap-1.5">
                <Download size={14} /> Descargar PDF
              </button>
            )}
            <span className={`text-[10px] font-bold px-3 py-1 rounded border inline-flex items-center gap-1.5 ${PILL[invoice.status] || PILL.PENDING}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${invoice.status === 'PAID' ? 'bg-green-300' : invoice.status === 'APPROVED' ? 'bg-green-400' : invoice.status === 'OC_PENDING' ? 'bg-blue-400' : invoice.status === 'DELETE_REQUESTED' ? 'bg-red-300' : 'bg-amber-500'}`} />
              {PILL_LABEL[invoice.status] || invoice.status}
            </span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_300px] gap-3.5">
        {/* ═══ LEFT: PDF + datos ═══ */}
        <div className="space-y-3.5">
          {/* Visor galería (ReviewTicket pattern) */}
          {pages.length > 0 ? (
            <div className="bg-zinc-950 border border-zinc-700 rounded-sm overflow-hidden">
              <div className="relative cursor-zoom-in group" onClick={() => setShowLightbox(true)}>
                <img src={pages[currentPage]} alt={`Página ${currentPage + 1}`} className="w-full max-h-96 object-contain bg-zinc-900" />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="bg-amber-500 text-zinc-950 p-3 rounded-full shadow-lg"><ZoomIn size={24} /></div>
                  </div>
                </div>
              </div>
              <div className="px-4 py-3 bg-zinc-900/80 border-t border-zinc-800 flex items-center justify-center">
                <div className="flex items-center gap-3">
                  <button onClick={() => setCurrentPage(p => Math.max(0, p - 1))} disabled={currentPage === 0 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"><ChevronLeft size={18} /></button>
                  <span className="text-sm font-mono text-zinc-300">{totalPages > 1 ? `${currentPage + 1}/${totalPages}` : invoice.invoice_number}</span>
                  <button onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))} disabled={currentPage === totalPages - 1 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"><ChevronRight size={18} /></button>
                </div>
              </div>
              {totalPages > 1 && (
                <div className="px-4 pb-3 bg-zinc-900/80 flex justify-center gap-1.5">
                  {pages.map((_, i) => (
                    <button key={i} onClick={() => setCurrentPage(i)} className={`w-2 h-2 rounded-full transition-colors ${i === currentPage ? 'bg-amber-500' : 'bg-zinc-600 hover:bg-zinc-400'}`} />
                  ))}
                </div>
              )}
            </div>
          ) : invoice.file_url && (
            <div className="bg-zinc-950 border border-zinc-700 rounded-sm overflow-hidden">
              <iframe src={invoice.file_url} title="PDF" className="w-full h-96 bg-zinc-900" />
            </div>
          )}

          {/* LIGHTBOX fullscreen (ReviewTicket pattern) */}
          {showLightbox && pages.length > 0 && (
            <div className="fixed inset-0 bg-black z-50 flex items-center justify-center backdrop-blur-sm"
              style={{ minHeight: '100dvh', paddingTop: 'env(safe-area-inset-top, 0px)', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
              onClick={() => setShowLightbox(false)}>
              <button onClick={(e) => { e.stopPropagation(); setShowLightbox(false); }}
                className="absolute top-4 right-4 text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700 z-10"
                style={{ marginTop: 'env(safe-area-inset-top, 0px)' }}><X size={32} /></button>
              {totalPages > 1 && currentPage > 0 && (
                <button onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p - 1); }}
                  className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center">
                  <ChevronLeft size={28} /></button>
              )}
              <img src={pages[currentPage]} alt={`Página ${currentPage + 1}`}
                className="max-w-full max-h-[90vh] object-contain shadow-2xl select-none"
                onClick={(e) => e.stopPropagation()} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd} />
              {totalPages > 1 && currentPage < totalPages - 1 && (
                <button onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p + 1); }}
                  className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center">
                  <ChevronRight size={28} /></button>
              )}
              {totalPages > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-900/80 px-4 py-2 rounded-full text-sm font-mono text-zinc-300 border border-zinc-700">
                  Página {currentPage + 1} / {totalPages}
                </div>
              )}
            </div>
          )}

          {/* Datos factura */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Datos de la factura</div>
            <div className={rowCls}><span className={labelCls}>Nº Factura</span><span className={`${valCls} ${monoCls} text-amber-400`}>{invoice.invoice_number}</span></div>
            <div className={rowCls}><span className={labelCls}>Fecha</span><span className={valCls}>{invoice.date}</span></div>
            <div className={rowCls}><span className={labelCls}>Proveedor</span><span className={valCls}>{invoice.provider_name}</span></div>
            <div className={rowCls}><span className={labelCls}>NIF/CIF</span><span className={`${valCls} ${monoCls}`}>{invoice.nif_cif || '—'}</span></div>
            <div className={rowCls}>
              <span className={labelCls}>OC</span>
              {invoice.oc_number
                ? <span className="text-[12px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{invoice.oc_number}</span>
                : <span className="text-[12px] px-1.5 py-[1px] rounded bg-blue-400/[.08] text-blue-400 border border-blue-400/15 font-semibold">Sin OC</span>
              }
            </div>
          </div>
        </div>

        {/* ═══ RIGHT: Importes + IA + acciones ═══ */}
        <div className="space-y-3.5">
          {/* Importes */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Importes</div>
            <div className={rowCls}><span className={labelCls}>Base imponible</span><span className={`${valCls} ${monoCls}`}>{invoice.base_amount?.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</span></div>
            <div className={rowCls}><span className={labelCls}>IVA ({((invoice.iva_percentage ?? 0) * 100).toFixed(0)}%)</span><span className={`${valCls} ${monoCls}`}>{invoice.iva_amount?.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</span></div>
            {(invoice.irpf_amount > 0) && (
              <div className={rowCls}><span className={labelCls}>IRPF ({((invoice.irpf_percentage ?? 0) * 100).toFixed(0)}%)</span><span className={`${valCls} ${monoCls} text-red-400`}>-{invoice.irpf_amount?.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</span></div>
            )}
            <div className="flex justify-between pt-3 mt-1 border-t border-zinc-700">
              <span className="text-xs font-semibold text-zinc-300">Total</span>
              <span className="font-mono text-base font-bold text-amber-400">{invoice.final_total?.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</span>
            </div>
          </div>

          {/* Resultado IA */}
          {iaResult && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
              <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Validación IA</div>
              {iaResult.valid ? (
                <div className="flex items-center gap-2 text-xs text-green-400">
                  <Check size={14} strokeWidth={2} /> Validación correcta
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-red-400 mb-2">
                  <AlertTriangle size={14} /> Validación con errores
                </div>
              )}
              {iaResult.errors?.length > 0 && (
                <div className="mt-2 space-y-1">
                  {iaResult.errors.map((err, i) => (
                    <div key={i} className="text-[11px] text-red-400 bg-red-400/[.06] border border-red-400/[.12] rounded p-2">{err}</div>
                  ))}
                </div>
              )}
              {iaResult.warnings?.length > 0 && (
                <div className="mt-2 space-y-1">
                  {iaResult.warnings.map((w, i) => (
                    <div key={i} className="text-[11px] text-amber-400 bg-amber-500/[.06] border border-amber-500/[.12] rounded p-2">{w}</div>
                  ))}
                </div>
              )}
              {/* IBAN match checklist */}
              {'iban_match' in iaResult && (
                <div className="mt-2">
                  {iaResult.iban_match === true && (
                    <div className="text-[12px] text-green-400 flex items-center gap-1.5">
                      <Check size={12} strokeWidth={2} /> IBAN matches registered account
                    </div>
                  )}
                  {iaResult.iban_match === false && (
                    <div className="text-[12px] text-red-400 flex items-center gap-1.5">
                      <AlertTriangle size={12} /> IBAN does NOT match registered account
                    </div>
                  )}
                  {iaResult.iban_match === null && (
                    <div className="text-[12px] text-zinc-500">— IBAN not found on invoice</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Borrado solicitado */}
          {invoice.status === 'DELETE_REQUESTED' && invoice.delete_reason && (
            <div className="bg-red-400/[.06] border border-red-400/[.12] rounded-md p-4">
              <div className="text-[9px] text-red-400 tracking-widest uppercase mb-2 font-semibold">Motivo de borrado solicitado</div>
              <p className="text-xs text-red-300">{invoice.delete_reason}</p>
            </div>
          )}

          {/* Acciones */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Acciones</div>
            {invoice.status === 'OC_PENDING' && (
              <div>
                <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded p-2.5 text-[11px] mb-3 flex items-start gap-2">
                  <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" />
                  La IA no detectó el OC en esta factura. Asígnalo manualmente.
                </div>
                <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Buscar OC o proyecto</label>
                <div className="relative mb-2">
                  <Search size={13} className="absolute left-2.5 top-2.5 text-zinc-500 pointer-events-none" />
                  <input
                    value={ocSearch}
                    onChange={e => setOcSearch(e.target.value)}
                    placeholder="Escribe OC o nombre de proyecto..."
                    className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] pl-8 pr-3 py-2 rounded focus:border-amber-500 outline-none"
                  />
                  {ocSuggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded-md overflow-hidden z-50 shadow-xl">
                      {ocSuggestions.map((s, i) => (
                        <div key={i} onClick={() => handleAssignOC(s.oc_number)}
                          className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs border-b border-white/[.04] last:border-0 flex items-center gap-2">
                          <span className="text-[11px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{s.oc_number}</span>
                          <span className="text-zinc-400 truncate">{s.label}{s.company_name ? ` · ${s.company_name}` : ''}</span>
                        </div>
                      ))}
                      <div onClick={() => handleAssignOC(ocSearch)}
                        className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-[12px] text-zinc-500 text-center border-t border-white/[.04]">
                        + Escribir OC personalizado
                      </div>
                    </div>
                  )}
                </div>
                {ocSearch.length >= 2 && ocSuggestions.length === 0 && (
                  <button onClick={() => handleAssignOC(ocSearch)} disabled={assigning}
                    className="w-full text-xs bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 mb-2">
                    {assigning ? 'Asignando...' : `Asignar "${ocSearch}" como OC`}
                  </button>
                )}
              </div>
            )}
            {invoice.status === 'PENDING' && (
              <button onClick={() => handleAction('APPROVED')} disabled={acting}
                className="w-full text-xs bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 mb-2">
                {acting ? 'Procesando...' : 'Aprobar'}
              </button>
            )}
            {invoice.status === 'APPROVED' && (
              <button onClick={() => handleAction('PAID')} disabled={acting}
                className="w-full text-xs text-zinc-300 border border-zinc-700 hover:bg-zinc-800 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 mb-2">
                {acting ? 'Procesando...' : 'Marcar como pagada'}
              </button>
            )}
            {(invoice.status === 'PENDING' || invoice.status === 'OC_PENDING' || invoice.status === 'APPROVED') && (
              <button onClick={() => setDeleteModal(true)} disabled={acting}
                className="w-full text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-400/25 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                <Trash2 size={13} /> Eliminar factura
              </button>
            )}
            {invoice.status === 'DELETE_REQUESTED' && (
              <div className="space-y-2">
                <button onClick={handleRejectDeletion} disabled={acting}
                  className="w-full text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/25 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                  <RotateCcw size={13} /> Rechazar borrado
                </button>
                <button onClick={() => setConfirmDeleteRequested(true)} disabled={acting}
                  className="w-full text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-400/25 font-semibold py-2.5 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                  <Trash2 size={13} /> Confirmar borrado
                </button>
              </div>
            )}
            {invoice.status === 'PAID' && (
              <p className="text-xs text-zinc-600 text-center py-2">Factura cerrada — no hay acciones disponibles</p>
            )}
          </div>
        </div>
      </div>

      {/* ═══ MODAL: Eliminar ═══ */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => { setDeleteModal(false); setDeleteReason(''); }}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">Eliminar factura</h3>
            <p className="text-xs text-zinc-500 mb-4">
              Factura <span className="font-mono text-zinc-300">{invoice.invoice_number}</span> de {invoice.supplier_name || invoice.provider_name}
            </p>
            <div className="mb-4">
              <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Motivo <span className="text-amber-500">*</span></label>
              <textarea value={deleteReason} onChange={e => setDeleteReason(e.target.value)} rows={3} placeholder="Motivo de la eliminación..."
                className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded focus:border-amber-500 outline-none resize-none" />
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setDeleteModal(false); setDeleteReason(''); }} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancelar</button>
              <button onClick={() => handleDelete(deleteReason)} disabled={!deleteReason.trim() || acting}
                className="text-xs px-4 py-2 rounded bg-red-500 hover:bg-red-400 text-white font-semibold transition-colors disabled:opacity-40">
                {acting ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Confirmar borrado DELETE_REQUESTED ═══ */}
      {confirmDeleteRequested && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => setConfirmDeleteRequested(false)}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">Eliminar factura</h3>
            <p className="text-xs text-zinc-500 mb-4">¿Confirmar borrado definitivo? El proveedor ya solicitó la eliminación.</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setConfirmDeleteRequested(false)} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancelar</button>
              <button onClick={() => { setConfirmDeleteRequested(false); handleDelete(null); }} disabled={acting}
                className="text-xs px-4 py-2 rounded bg-red-500 hover:bg-red-400 text-white font-semibold transition-colors disabled:opacity-40">
                {acting ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoiceDetail;
