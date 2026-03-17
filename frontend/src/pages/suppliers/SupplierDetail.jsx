import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, UserX, Link2, ExternalLink, Check, Download, Search, X, Edit3, Mic, Trash2 } from 'lucide-react';
import { getSupplier, updateSupplier, deactivateSupplier, reactivateSupplier, assignOC, addSupplierNote, getAllInvoices, getNotifications, getBankCertUrl, updateInvoiceStatus, deleteInvoice, exportSupplierExcel } from '../../services/suppliersApi';
import useVoiceSearch from '../../hooks/useVoiceSearch';
import useClickOutside from '../../hooks/useClickOutside';

const PILL = {
  PENDING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  OC_PENDING: 'bg-zinc-700/50 text-zinc-400 border-zinc-700',
  APPROVED: 'bg-green-400/10 text-green-400 border-green-400/20',
  PAID: 'bg-green-300/10 text-green-300 border-green-300/20',
  REJECTED: 'bg-red-400/10 text-red-400 border-red-400/20',
  DELETE_REQUESTED: 'bg-red-300/10 text-red-300 border-red-300/20',
};
const PILL_LABEL = {
  PENDING: 'Pendiente', OC_PENDING: 'OC pendiente', APPROVED: 'Aprobada',
  PAID: 'Pagada', REJECTED: 'Rechazada', DELETE_REQUESTED: 'Borrado solicitado',
};
const STATUS_LABEL = { ACTIVE: 'Activo', NEW: 'Nuevo', DEACTIVATED: 'Desactivado' };
const HISTORY_DOT = {
  NEW_INVOICE: 'bg-blue-400', REGISTRATION: 'bg-green-400', APPROVED: 'bg-green-400',
  PAID: 'bg-green-300', REJECTED: 'bg-red-400', DELETED: 'bg-red-400',
  OC_LINKED: 'bg-purple-400', IA_REJECTED: 'bg-amber-500',
};

const SupplierDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [supplier, setSupplier] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  // Invoice search (ProjectView pattern)
  const [invoiceSearch, setInvoiceSearch] = useState('');
  const [invoiceFilter, setInvoiceFilter] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);

  // Edit modal
  const [editModal, setEditModal] = useState(false);
  const [editForm, setEditForm] = useState({ supplier_type: '', oc_number: '' });
  const [editSaving, setEditSaving] = useState(false);

  // Delete invoice modal
  const [deleteModal, setDeleteModal] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');

  // Voice search
  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => {
      setInvoiceSearch(transcript);
      setShowSuggestions(false);
    }, []),
  });
  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));

  const load = () => {
    Promise.all([
      getSupplier(id),
      getAllInvoices({ supplier_id: id }),
      getNotifications({ limit: 20 }),
    ]).then(([s, inv, notifs]) => {
      setSupplier(s.data);
      setInvoices(inv.data || []);
      setHistory((notifs.data || []).filter(n => n.related_supplier_id === parseInt(id)));
    }).catch(() => navigate('/suppliers/list'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const saved = localStorage.getItem(`recentSearches_supplier_${id}`);
    if (saved) setRecentSearches(JSON.parse(saved));
  }, [id]);

  // --- Handlers ---
  const handleDeactivate = async () => {
    if (!confirm('¿Desactivar este proveedor? Se invalidarán todos sus tokens.')) return;
    await deactivateSupplier(id);
    load();
  };

  const handleReactivate = async () => {
    if (!confirm('¿Reactivar este proveedor?')) return;
    await reactivateSupplier(id);
    load();
  };

  const handleViewCert = async () => {
    try {
      const { data } = await getBankCertUrl(id);
      window.open(data.url, '_blank');
    } catch { alert('No se pudo cargar el certificado bancario'); }
  };

  const handleAddNote = async () => {
    if (!note.trim()) return;
    setSaving(true);
    await addSupplierNote(id, note);
    setNote('');
    load();
    setSaving(false);
  };

  const handleDeleteNote = async (lineIndex) => {
    if (!supplier.notes_internal) return;
    const lines = supplier.notes_internal.split('\n');
    const updated = lines.filter((_, i) => i !== lineIndex).join('\n').trim();
    await updateSupplier(id, { notes_internal: updated || null });
    load();
  };

  const handleInvoiceAction = async (invoiceId, status) => {
    try {
      await updateInvoiceStatus(invoiceId, { status });
      load();
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
  };

  const handleDeleteInvoice = async () => {
    if (!deleteModal || !deleteReason.trim()) return;
    try {
      await deleteInvoice(deleteModal.id);
      load();
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
    setDeleteModal(null);
    setDeleteReason('');
  };

  const handleExportExcel = async () => {
    try {
      const response = await exportSupplierExcel(id);
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${supplier.name.replace(/\s/g, '_')}_facturas.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch { alert('Error al exportar Excel'); }
  };

  const handleEditSave = async () => {
    setEditSaving(true);
    try {
      await updateSupplier(id, { supplier_type: editForm.supplier_type });
      if (editForm.oc_number.trim() && editForm.oc_number.trim() !== (supplier.oc_number || '')) {
        await assignOC(id, editForm.oc_number.trim());
      }
      setEditModal(false);
      load();
    } catch (e) { alert(e.response?.data?.detail || 'Error al guardar'); }
    setEditSaving(false);
  };

  const openEditModal = () => {
    setEditForm({
      supplier_type: supplier.supplier_type || 'GENERAL',
      oc_number: supplier.oc_number || '',
    });
    setEditModal(true);
  };

  // Search helpers (ProjectView pattern)
  const handleSearchChange = (value) => {
    setInvoiceSearch(value);
    setShowSuggestions(value.length > 0);
  };
  const clearSearch = () => { setInvoiceSearch(''); setShowSuggestions(false); };
  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem(`recentSearches_supplier_${id}`, JSON.stringify(updated));
  };

  const timeAgo = (d) => {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}min`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return new Date(d).toLocaleDateString('es-ES');
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!supplier) return null;

  const initials = supplier.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  // Filter invoices
  const filtered = invoices.filter(inv => {
    if (invoiceFilter && inv.status !== invoiceFilter) return false;
    if (!invoiceSearch) return true;
    const q = invoiceSearch.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) || inv.oc_number?.toLowerCase().includes(q) || inv.provider_name?.toLowerCase().includes(q);
  });

  // Suggestions for search dropdown
  const suggestions = invoiceSearch ? invoices.filter(inv => {
    const q = invoiceSearch.toLowerCase();
    return inv.invoice_number?.toLowerCase().includes(q) || inv.oc_number?.toLowerCase().includes(q);
  }).slice(0, 5) : [];

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2.5 rounded focus:border-amber-500 outline-none";
  const labelCls = "text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">
          <span onClick={() => navigate('/suppliers/list')} className="text-zinc-500 cursor-pointer hover:text-amber-400 transition-colors">PROVEEDORES</span>
          {' / '}{supplier.name.toUpperCase()}
        </h1>
        <button onClick={openEditModal} className="text-[13px] text-zinc-400 border border-zinc-700 px-3 py-1.5 rounded hover:bg-zinc-800 transition-colors flex items-center gap-1">
          <Edit3 size={13} /> Editar datos
        </button>
      </div>

      <div className="grid lg:grid-cols-[320px_1fr] gap-3.5">
        {/* ═══ LEFT: Supplier card ═══ */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
          {/* Avatar + nombre en horizontal */}
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-amber-500 rounded-md flex items-center justify-center font-['Bebas_Neue'] text-xl text-zinc-950 flex-shrink-0">{initials}</div>
            <div>
              <div className="font-['Bebas_Neue'] text-[22px] tracking-wide text-zinc-100">{supplier.name.toUpperCase()}</div>
              <div className="flex gap-1.5 flex-wrap items-center mt-1">
                <span className={`text-[13px] font-bold px-[8px] py-[3px] rounded border ${supplier.is_active ? 'bg-green-400/10 text-green-400 border-green-400/20' : 'bg-zinc-700/50 text-zinc-500 border-zinc-700'}`}>
                  {STATUS_LABEL[supplier.status] || supplier.status}
                </span>
                <span className={`text-[13px] font-bold px-[8px] py-[3px] rounded border ${supplier.supplier_type === 'INFLUENCER' ? 'bg-purple-400/10 text-purple-400 border-purple-400/20' : supplier.supplier_type === 'MIXED' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-blue-400/10 text-blue-400 border-blue-400/20'}`}>
                  {supplier.supplier_type === 'INFLUENCER' ? 'Talent' : supplier.supplier_type === 'GENERAL' ? 'General' : 'Mixed'}
                </span>
              </div>
            </div>
          </div>

          {supplier.oc_number && (
            <div className="mb-3 inline-flex items-center gap-1.5 bg-purple-400/[.08] text-purple-400 text-[12px] font-medium px-[10px] py-[4px] rounded border border-purple-400/15 font-mono">
              <Link2 size={12} />{supplier.oc_number}
            </div>
          )}

          <hr className="border-white/[.04] my-2" />

          {/* Data rows */}
          {[
            ['Empresa', supplier.company_name || 'Todas'],
            ['Email', supplier.email, false, true],
            ['NIF/CIF', supplier.nif_cif, true],
            ['Teléfono', supplier.phone],
            ['Dirección', supplier.address],
            ['IBAN', supplier.iban, true, true],
            ['Cert. bancario', supplier.bank_cert_url ? 'pdf' : null],
            ['Alta', supplier.created_at ? new Date(supplier.created_at).toLocaleDateString('es-ES') : '—', true],
          ].map(([label, val, mono, amber]) => (
            <div key={label} className="flex justify-between py-2 border-b border-white/[.04] last:border-0">
              <span className="text-[13px] text-zinc-500">{label}</span>
              {val === 'pdf' ? (
                <button onClick={handleViewCert} className="text-[13px] text-red-400 cursor-pointer flex items-center gap-1 hover:text-red-300 transition-colors">Ver PDF → <ExternalLink size={10} /></button>
              ) : (
                <span className={`text-right max-w-[175px] break-all text-[13px] ${mono ? 'font-mono' : ''} ${amber ? 'text-amber-400' : 'text-zinc-300'}`}>
                  {val || '—'}
                </span>
              )}
            </div>
          ))}

          {/* Notas */}
          {supplier.notes_internal && supplier.notes_internal.split('\n').filter(Boolean).map((line, i) => (
            <div key={i} className="flex items-start gap-1.5 bg-zinc-800 rounded p-2 text-[13px] text-zinc-400 mt-1.5 border-l-2 border-amber-500 group">
              <span className="flex-1 whitespace-pre-wrap">{line}</span>
              <button onClick={() => handleDeleteNote(i)} className="text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" title="Eliminar nota">
                <X size={11} />
              </button>
            </div>
          ))}

          <hr className="border-white/[.04] my-3" />

          {/* Historial de eventos */}
          {history.length > 0 && (
            <div className="mb-3">
              <div className="text-[11px] text-zinc-500 tracking-widest uppercase mb-2">Historial de eventos</div>
              {history.slice(0, 5).map(h => (
                <div key={h.id} className="flex items-start gap-2 py-2 border-b border-white/[.04] last:border-0">
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${HISTORY_DOT[h.event_type] || 'bg-zinc-600'}`} />
                  <div>
                    <div className="text-[13px] text-zinc-300">{h.message || h.title}</div>
                    <div className="text-[12px] text-zinc-600">{timeAgo(h.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Añadir nota + acciones */}
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Añadir nota interna..."
            rows={2}
            className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-2.5 py-2 rounded focus:border-amber-500 outline-none resize-none"
          />
          <div className="flex gap-1.5 mt-1.5 flex-wrap">
            <button onClick={handleAddNote} disabled={saving || !note.trim()} className="text-[13px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-[14px] py-[8px] rounded border border-zinc-700 transition-colors disabled:opacity-40 flex items-center gap-1">
              <Save size={13} /> Añadir nota
            </button>
            {supplier.is_active ? (
              <button onClick={handleDeactivate} className="text-[13px] text-red-400 border border-red-400/25 hover:bg-red-400/[.08] px-[14px] py-[8px] rounded transition-colors flex items-center gap-1">
                <UserX size={13} /> Desactivar
              </button>
            ) : (
              <button onClick={handleReactivate} className="text-[13px] text-green-400 border border-green-400/25 hover:bg-green-400/[.08] px-[14px] py-[8px] rounded transition-colors flex items-center gap-1">
                <Check size={13} /> Activar
              </button>
            )}
          </div>
        </div>

        {/* ═══ RIGHT: Facturas ═══ */}
        <div>
          {/* Buscador ProjectView pattern */}
          <div className="flex items-center gap-2.5 mb-3 flex-wrap">
            <div className="relative w-[300px]" ref={searchRef}>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-zinc-500 pointer-events-none" size={14} />
                <input
                  type="text"
                  placeholder="Buscar factura, OC, proveedor..."
                  value={invoiceSearch}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onFocus={() => (invoiceSearch || recentSearches.length > 0) && setShowSuggestions(true)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && invoiceSearch.trim()) { saveRecentSearch(invoiceSearch); setShowSuggestions(false); } }}
                  className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[13px] pl-9 pr-14 py-2 rounded-sm focus:border-amber-500 outline-none"
                />
                <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
                  {invoiceSearch && (
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
              {/* Dropdown sugerencias */}
              {showSuggestions && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded shadow-xl max-h-64 overflow-y-auto z-50">
                  {invoiceSearch && suggestions.length > 0 && (
                    <>
                      <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Facturas encontradas</div>
                      {suggestions.map(inv => (
                        <div key={inv.id} onClick={() => { setInvoiceSearch(inv.invoice_number); saveRecentSearch(inv.invoice_number); setShowSuggestions(false); }}
                          className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-300 border-b border-zinc-800/50 last:border-0">
                          <span className="font-mono text-amber-400">{inv.invoice_number}</span>
                          {inv.oc_number && <span className="text-zinc-500 ml-2">· {inv.oc_number}</span>}
                        </div>
                      ))}
                    </>
                  )}
                  {!invoiceSearch && recentSearches.length > 0 && (
                    <>
                      <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Búsquedas recientes</div>
                      {recentSearches.map((term, i) => (
                        <div key={i} onClick={() => { setInvoiceSearch(term); setShowSuggestions(false); }}
                          className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-400 border-b border-zinc-800/50 last:border-0">
                          {term}
                        </div>
                      ))}
                    </>
                  )}
                  {invoiceSearch && suggestions.length === 0 && (
                    <div className="px-3 py-3 text-xs text-zinc-600 text-center">Sin resultados</div>
                  )}
                </div>
              )}
            </div>
            <div className="flex gap-1.5 flex-1 justify-end">
              {[
                { key: '', label: 'Todas' },
                { key: 'PENDING', label: 'Pendientes' },
                { key: 'APPROVED', label: 'Aprobadas' },
                { key: 'PAID', label: 'Pagadas' },
              ].map(f => (
                <button
                  key={f.key}
                  onClick={() => setInvoiceFilter(f.key)}
                  className={`text-[13px] px-3 py-1 rounded-full border transition-all ${
                    invoiceFilter === f.key
                      ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Lista facturas */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            {filtered.length === 0 ? (
              <p className="text-xs text-zinc-600 text-center py-6">Sin facturas</p>
            ) : (
              <div className="space-y-1">
                {filtered.map(inv => (
                  <div
                    key={inv.id}
                    onClick={() => navigate(`/suppliers/invoices/${inv.id}?from=supplier&supplierId=${id}`)}
                    className="grid items-center gap-3 px-[12px] py-[12px] rounded hover:bg-white/[.02] transition-colors cursor-pointer"
                    style={{ gridTemplateColumns: '32px 200px 200px 130px auto 1fr auto' }}
                  >
                    {/* Icono */}
                    <div className="w-7 h-7 bg-red-400/[.08] rounded flex items-center justify-center border border-red-400/[.12] flex-shrink-0">
                      <svg className="w-3.5 h-3.5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </div>
                    {/* Nombre factura */}
                    <div className="text-[13px] font-semibold text-zinc-200 font-mono truncate">
                      {inv.invoice_number}
                    </div>
                    {/* OC */}
                    <div>
                      {inv.oc_number
                        ? <span className="text-[13px] px-[7px] py-[2px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{inv.oc_number}</span>
                        : <span className="text-[13px] text-zinc-600">—</span>
                      }
                    </div>
                    {/* Fecha */}
                    <div className="text-[11px] text-zinc-400">{inv.date}</div>
                    {/* Importe */}
                    <div className="font-mono text-[12px] font-medium text-zinc-200 whitespace-nowrap">{inv.final_total?.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €</div>
                    {/* Estado — centrado en su columna 1fr */}
                    <div className="flex justify-center">
                      <span className={`text-[12px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 whitespace-nowrap ${PILL[inv.status] || PILL.PENDING}`}>
                        <span className={`w-1 h-1 rounded-full ${inv.status === 'PAID' ? 'bg-green-300' : inv.status === 'APPROVED' ? 'bg-green-400' : inv.status === 'REJECTED' ? 'bg-red-400' : 'bg-amber-500'}`} />
                        {PILL_LABEL[inv.status] || inv.status}
                      </span>
                    </div>
                    {/* Acciones — pegadas a la derecha, misma altura */}
                    <div className="flex items-center gap-1 justify-end">
                      {inv.status === 'PENDING' && (
                        <button onClick={(e) => { e.stopPropagation(); handleInvoiceAction(inv.id, 'APPROVED'); }} className="text-[13px] bg-amber-500 text-zinc-950 font-semibold px-2.5 py-1 rounded hover:bg-amber-400 transition-colors">Aprobar</button>
                      )}
                      {inv.status === 'APPROVED' && (
                        <button onClick={(e) => { e.stopPropagation(); handleInvoiceAction(inv.id, 'PAID'); }} className="text-[13px] text-zinc-400 border border-zinc-700 px-2.5 py-1 rounded hover:bg-zinc-800 transition-colors">Marcar pagada</button>
                      )}
                      {inv.status === 'PAID' && (
                        <span className="text-[13px] text-zinc-600">Cerrada</span>
                      )}
                      {(inv.status === 'PENDING' || inv.status === 'APPROVED') && (
                        <button onClick={(e) => { e.stopPropagation(); setDeleteModal(inv); }} className="text-[13px] px-2.5 py-1 flex items-center justify-center border border-red-400/20 rounded text-red-400/60 hover:text-red-400 hover:bg-red-400/10 transition-colors">
                          <Trash2 size={13} strokeWidth={1.5} />
                        </button>
                      )}
                      {inv.status === 'PAID' && (
                        <div className="text-[13px] px-2.5 py-1 flex items-center justify-center">
                          <Trash2 size={13} className="text-zinc-800" strokeWidth={1.5} />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Exportar a Excel */}
          {invoices.length > 0 && (
            <div className="flex justify-end mt-2">
              <button onClick={handleExportExcel} className="text-[13px] text-zinc-400 border border-zinc-700 hover:bg-zinc-800 px-3 py-1.5 rounded transition-colors flex items-center gap-1">
                <Download size={13} /> Exportar a Excel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ═══ MODAL: Editar datos ═══ */}
      {editModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => setEditModal(false)}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-4">Editar proveedor</h3>
            <div className="space-y-3">
              <div>
                <label className={labelCls}>Tipo de proveedor</label>
                <select value={editForm.supplier_type} onChange={e => setEditForm(f => ({ ...f, supplier_type: e.target.value }))}
                  className={`${inputCls} appearance-none`}>
                  <option value="GENERAL">General</option>
                  <option value="INFLUENCER">Talent / Influencer</option>
                  <option value="MIXED">Mixed</option>
                </select>
              </div>
              <div>
                <label className={labelCls}>OC asignado</label>
                <input value={editForm.oc_number} onChange={e => setEditForm(f => ({ ...f, oc_number: e.target.value }))} placeholder="OC-MGMTINT2026047" className={`${inputCls} font-mono`} />
                <div className="text-[9px] text-zinc-600 mt-1">El OC debe existir en el sistema. Dejar vacío para no cambiar.</div>
              </div>
            </div>
            <div className="flex gap-2 justify-end mt-4">
              <button onClick={() => setEditModal(false)} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancelar</button>
              <button onClick={handleEditSave} disabled={editSaving}
                className="text-xs px-4 py-2 rounded bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold transition-colors disabled:opacity-40">
                {editSaving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ MODAL: Eliminar factura ═══ */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/70 z-[200] flex items-center justify-center" onClick={() => { setDeleteModal(null); setDeleteReason(''); }}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-[420px] max-w-[95vw] p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-['Bebas_Neue'] text-base tracking-wider text-zinc-100 mb-1">Eliminar factura</h3>
            <p className="text-xs text-zinc-500 mb-4">
              Factura <span className="font-mono text-zinc-300">{deleteModal.invoice_number}</span> de {deleteModal.supplier_name || supplier.name}
            </p>
            <div className="mb-4">
              <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Motivo <span className="text-amber-500">*</span></label>
              <textarea value={deleteReason} onChange={e => setDeleteReason(e.target.value)} rows={3} placeholder="Motivo de la eliminación..."
                className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded focus:border-amber-500 outline-none resize-none" />
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setDeleteModal(null); setDeleteReason(''); }} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancelar</button>
              <button onClick={handleDeleteInvoice} disabled={!deleteReason.trim()}
                className="text-xs px-4 py-2 rounded bg-red-500 hover:bg-red-400 text-white font-semibold transition-colors disabled:opacity-40">Eliminar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplierDetail;
