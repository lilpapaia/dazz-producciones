import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
const PAGE_SIZE = 20;

const InvoicesList = () => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list');
  const [statusFilter, setStatusFilter] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [search, setSearch] = useState('');
  const [actionModal, setActionModal] = useState(null);
  const [reason, setReason] = useState('');
  const [page, setPage] = useState(0);
  const [totalLoaded, setTotalLoaded] = useState(0);

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
    if (!actionModal) return;
    const { invoice, action } = actionModal;
    try {
      if (action === 'approve') await updateInvoiceStatus(invoice.id, { status: 'APPROVED' });
      else if (action === 'pay') await updateInvoiceStatus(invoice.id, { status: 'PAID' });
      else if (action === 'reject') { if (!reason.trim()) return; await updateInvoiceStatus(invoice.id, { status: 'REJECTED', reason }); }
      else if (action === 'delete') await deleteInvoice(invoice.id);
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
    setActionModal(null); setReason(''); load();
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100">Facturas</h1>
        <div className="flex gap-1 bg-zinc-800 rounded p-0.5">
          <button onClick={() => setView('list')} className={`text-[10px] px-2.5 py-1 rounded flex items-center gap-1 ${view === 'list' ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500'}`}>
            <List size={12} /> Lista
          </button>
          <button onClick={() => setView('kanban')} className={`text-[10px] px-2.5 py-1 rounded flex items-center gap-1 ${view === 'kanban' ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500'}`}>
            <Columns3 size={12} /> Kanban
          </button>
        </div>
      </div>

      {/* Filters — dropdowns (I2) */}
      <div className="flex gap-2 mb-3.5 flex-wrap items-center">
        <div className="relative max-w-[220px] flex-1">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
          <input placeholder="Buscar factura, OC, proveedor..." value={search} onChange={e => setSearch(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[11px] pl-8 pr-3 py-2 rounded focus:border-amber-500 outline-none" />
        </div>
        <select value={companyFilter} onChange={e => setCompanyFilter(e.target.value)}
          className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-[11px] px-2.5 py-2 rounded outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}>
          <option value="">Todas las empresas</option>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-[11px] px-2.5 py-2 rounded outline-none appearance-none pr-7 bg-no-repeat bg-[right_8px_center]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")" }}>
          <option value="">Todos los estados</option>
          <option value="PENDING">Pendiente</option>
          <option value="APPROVED">Aprobada</option>
          <option value="PAID">Pagada</option>
          <option value="REJECTED">Rechazada</option>
        </select>
      </div>

      {/* LIST VIEW */}
      {view === 'list' && (
        <>
          <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-x-auto">
            <table className="w-full min-w-[650px]">
              <thead>
                <tr>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Nº Factura</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Proveedor</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Proyecto · OC</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium w-10">IA</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Importe</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium">Estado</th>
                  <th className="bg-zinc-800 px-3 py-2.5 text-left text-[9px] text-zinc-400 tracking-widest uppercase font-medium w-[140px]">Acción</th>
                  <th className="bg-zinc-800 px-3 py-2.5 w-9"></th>
                </tr>
              </thead>
              <tbody>
                {paged.map(inv => {
                  const pill = PILL[inv.status] || PILL.PENDING;
                  return (
                    <tr key={inv.id} onClick={() => navigate(`/suppliers/invoices/${inv.id}?from=list`)} className="hover:bg-white/[.02] transition-colors cursor-pointer">
                      <td className="px-3 py-2.5 border-b border-white/[.04] font-mono text-[11px] text-zinc-200">
                        {inv.invoice_number}
                        {inv.from_supplier_portal && <span className="ml-1.5 text-[8px] px-1.5 py-[1px] rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-sans font-bold">PORTAL</span>}
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04] text-xs text-zinc-200">{inv.supplier_name}</td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        <span className="text-[9px] px-1.5 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{inv.oc_number}</span>
                      </td>
                      {/* IA column (I1) */}
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        <span className="text-[10px] text-green-400 flex items-center gap-0.5"><Check size={11} strokeWidth={2} />ok</span>
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04] font-mono text-xs text-zinc-200">{inv.final_total?.toFixed(2)} EUR</td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${pill.cls}`}>
                          <span className={`w-1 h-1 rounded-full ${pill.dot}`} />{inv.status}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        {inv.status === 'PENDING' && (
                          <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'approve' }); }} className="text-[10px] bg-amber-500 text-zinc-950 font-semibold px-2.5 py-1 rounded transition-colors hover:bg-amber-400">Aprobar</button>
                        )}
                        {inv.status === 'APPROVED' && (
                          <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'pay' }); }} className="text-[10px] text-zinc-400 border border-zinc-700 px-2.5 py-1 rounded hover:bg-zinc-800 transition-colors">Marcar pagada</button>
                        )}
                        {inv.status === 'PAID' && <span className="text-[10px] text-zinc-600">Cerrada</span>}
                      </td>
                      <td className="px-3 py-2.5 border-b border-white/[.04]">
                        <div className="flex gap-1">
                          {inv.file_url && <button onClick={(e) => { e.stopPropagation(); window.open(inv.file_url, '_blank'); }} className="p-1 text-zinc-600 hover:text-zinc-300 transition-colors"><ExternalLink size={12} /></button>}
                          {inv.status === 'PENDING' && <button onClick={(e) => { e.stopPropagation(); setActionModal({ invoice: inv, action: 'reject' }); }} className="p-1 text-red-400/60 hover:text-red-400 transition-colors"><X size={12} /></button>}
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {paged.length === 0 && <tr><td colSpan="8" className="text-center py-8 text-xs text-zinc-600">Sin facturas</td></tr>}
              </tbody>
            </table>
          </div>
          {/* Pagination (I3) */}
          <div className="flex items-center justify-between mt-2 text-[11px] text-zinc-500">
            <span>Mostrando {Math.min(page * PAGE_SIZE + 1, filtered.length)}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} de {filtered.length} facturas</span>
            {totalPages > 1 && (
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="px-2.5 py-1 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">← Anterior</button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => (
                  <button key={i} onClick={() => setPage(i)} className={`px-2.5 py-1 rounded border transition-colors ${page === i ? 'bg-zinc-800 text-zinc-200 border-zinc-600' : 'border-zinc-700 text-zinc-500 hover:bg-zinc-800'}`}>{i + 1}</button>
                ))}
                <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-2.5 py-1 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">Siguiente →</button>
              </div>
            )}
          </div>
        </>
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
                {colInvoices.slice(0, 10).map(inv => (
                  <div key={inv.id} className="bg-zinc-800 border border-zinc-700 rounded p-2.5 mb-1.5 cursor-pointer hover:border-amber-500 transition-colors">
                    <div className="text-[10px] text-zinc-500 font-mono">{inv.invoice_number}</div>
                    <div className="text-xs font-medium text-zinc-200 mt-0.5">{inv.supplier_name}</div>
                    <div className="font-mono text-[13px] text-zinc-100 mt-0.5">{inv.final_total?.toFixed(2)} EUR</div>
                    <div className="text-[10px] text-zinc-500 mt-1 pt-1 border-t border-zinc-700">OC: <span className="text-amber-400">{inv.oc_number}</span></div>
                    <div className="flex gap-1 mt-1.5">
                      {col === 'PENDING' && <>
                        <button onClick={() => setActionModal({ invoice: inv, action: 'approve' })} className="text-[9px] text-green-400 border border-green-400/25 px-1.5 py-0.5 rounded hover:bg-green-400/10">Aprobar</button>
                        <button onClick={() => setActionModal({ invoice: inv, action: 'reject' })} className="text-[9px] text-red-400 border border-red-400/25 px-1.5 py-0.5 rounded hover:bg-red-400/10">Rechazar</button>
                      </>}
                      {col === 'APPROVED' && <button onClick={() => setActionModal({ invoice: inv, action: 'pay' })} className="text-[9px] text-green-300 border border-green-300/25 px-1.5 py-0.5 rounded hover:bg-green-300/10">Pagada</button>}
                    </div>
                  </div>
                ))}
                {colInvoices.length > 10 && <div className="text-[10px] text-zinc-600 text-center py-2 font-mono">+ {colInvoices.length - 10} más</div>}
                {colInvoices.length === 0 && <div className="text-[10px] text-zinc-700 text-center py-4">Vacío</div>}
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
              {actionModal.action === 'approve' && 'Aprobar factura'}
              {actionModal.action === 'pay' && 'Marcar como pagada'}
              {actionModal.action === 'reject' && 'Rechazar factura'}
            </h3>
            <p className="text-xs text-zinc-500 mb-4">
              Factura <span className="font-mono text-zinc-300">{actionModal.invoice.invoice_number}</span> de {actionModal.invoice.supplier_name}
            </p>
            {actionModal.action === 'reject' && (
              <div className="mb-4">
                <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">Motivo <span className="text-amber-500">*</span></label>
                <textarea value={reason} onChange={e => setReason(e.target.value)} rows={3} placeholder="Explica el motivo..." className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2 rounded focus:border-amber-500 outline-none resize-none" />
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setActionModal(null); setReason(''); }} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Cancelar</button>
              <button onClick={handleAction} disabled={actionModal.action === 'reject' && !reason.trim()}
                className={`text-xs px-4 py-2 rounded font-semibold transition-colors disabled:opacity-40 ${actionModal.action === 'reject' ? 'bg-red-500 hover:bg-red-400 text-white' : 'bg-amber-500 hover:bg-amber-400 text-zinc-950'}`}>
                {actionModal.action === 'approve' ? 'Aprobar' : actionModal.action === 'pay' ? 'Confirmar pago' : 'Rechazar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoicesList;
