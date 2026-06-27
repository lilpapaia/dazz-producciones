import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getGuestProject, getGuestTickets, deleteGuestTicket, downloadGuestExcel } from '../../services/shareApi';
import { Upload, Trash2, Search, X, Mic, Clock, Download, LogOut } from 'lucide-react';
import { useExternalSession } from '../../context/ExternalSessionContext';
import { showSuccess, showError } from '../../utils/toast';
import ConfirmDialog from '../../components/ConfirmDialog';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import StatusBadge from '../../components/common/StatusBadge';
import { getCurrencySymbol } from '../../utils/currency';
import EmptyState from '../../components/common/EmptyState';
import useVoiceSearch from '../../hooks/useVoiceSearch';
import useClickOutside from '../../hooks/useClickOutside';

// FEAT-09: vista simplificada del proyecto para el externo (sin Navbar, sin info
// de proyecto/presupuesto, sin cerrar/reabrir/eliminar). Usa shareApi y el JWT guest.
const ExternalProjectView = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { guestName, logoutGuest } = useExternalSession();

  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ticketsError, setTicketsError] = useState(false);
  const [deleteTicketId, setDeleteTicketId] = useState(null);
  const [downloadingExcel, setDownloadingExcel] = useState(false);

  // Búsqueda tickets
  const [ticketSearch, setTicketSearch] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);
  const RECENT_KEY = `recentSearches_share_${token}`;

  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => {
      setTicketSearch(transcript);
      const saved = localStorage.getItem(RECENT_KEY);
      const recent = saved ? JSON.parse(saved) : [];
      const updated = [transcript, ...recent.filter(s => s !== transcript)].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
    }, [RECENT_KEY]),
  });

  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));

  useEffect(() => {
    loadProject();
    loadTickets();
    const saved = localStorage.getItem(RECENT_KEY);
    if (saved) setRecentSearches(JSON.parse(saved));
  }, []);

  const loadProject = async () => {
    try {
      const response = await getGuestProject();
      setProject(response.data);
    } catch {
      showError('Error al cargar proyecto');
    } finally {
      setLoading(false);
    }
  };

  const loadTickets = async () => {
    try {
      setTicketsError(false);
      const response = await getGuestTickets();
      setTickets(response.data);
    } catch {
      setTicketsError(true);
    }
  };

  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
  };

  const handleSearchChange = (value) => {
    setTicketSearch(value);
    setShowSuggestions(value.length > 0);
  };

  const handleSearchSubmit = () => {
    if (ticketSearch.trim()) {
      saveRecentSearch(ticketSearch);
      setShowSuggestions(false);
    }
  };

  const clearSearch = () => {
    setTicketSearch('');
    setShowSuggestions(false);
  };

  const confirmDeleteTicket = async () => {
    try {
      await deleteGuestTicket(deleteTicketId);
      showSuccess('Ticket eliminado');
      loadTickets();
      loadProject();
    } catch (error) {
      showError(error.response?.data?.detail || 'Error al eliminar ticket');
    }
    setDeleteTicketId(null);
  };

  const handleDownloadExcel = async () => {
    setDownloadingExcel(true);
    try {
      const res = await downloadGuestExcel();
      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project?.creative_code || 'proyecto'}_GASTOS.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      showError('Error al descargar Excel');
    } finally {
      setDownloadingExcel(false);
    }
  };

  const handleLogout = () => {
    logoutGuest();
    navigate(`/share/${token}`, { replace: true });
  };

  const filteredTickets = tickets.filter(t => {
    if (!ticketSearch) return true;
    const search = ticketSearch.toLowerCase();
    return (
      t.provider.toLowerCase().includes(search) ||
      t.final_total.toString().includes(ticketSearch) ||
      t.base_amount.toString().includes(ticketSearch) ||
      t.invoice_number?.toLowerCase().includes(search) ||
      t.date?.includes(ticketSearch)
    );
  });

  const suggestions = filteredTickets.slice(0, 5);

  if (loading) return <LoadingSpinner size="lg" fullPage />;
  if (!project) return null;

  const isClosed = project.status === 'cerrado';

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* MINI HEADER (en vez de Navbar) */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between gap-3">
            {/* Izquierda: logo + empresa */}
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-amber-500 text-xl leading-none">✱</span>
              <span className="font-bebas tracking-wider text-lg truncate">
                {project.company_name || 'DAZZ CREATIVE'}
              </span>
            </div>
            {/* Derecha: bienvenida + salir */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-sm text-zinc-400 hidden sm:inline">
                Bienvenido, <span className="text-zinc-200">{guestName}</span>
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-zinc-400 hover:text-red-400 transition-colors text-sm"
                title="Salir"
              >
                <LogOut size={18} />
                <span className="hidden sm:inline">Salir</span>
              </button>
            </div>
          </div>

          {/* Proyecto: código + descripción + importe */}
          <div className="mt-3 flex flex-col md:flex-row md:items-end md:justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bebas tracking-wider">{project.creative_code}</h1>
                <StatusBadge type="project" value={project.status} />
              </div>
              <p className="text-sm text-zinc-300 truncate">{project.description}</p>
            </div>
            <div className="text-left md:text-right flex-shrink-0">
              <p className="text-3xl font-bold text-amber-500 leading-none">{project.total_amount?.toFixed(2)}€</p>
              <p className="text-xs text-zinc-500 mt-1">{project.tickets_count} tickets</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-8">
        {/* Acciones + búsqueda */}
        <div className="flex flex-col md:flex-row md:items-center gap-3 mb-6">
          <div className="w-full md:w-auto flex gap-2">
            <button
              onClick={() => navigate(`/share/${token}/upload`)}
              disabled={isClosed}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
            >
              <Upload size={16} />
              SUBIR
            </button>

            <button
              onClick={handleDownloadExcel}
              disabled={downloadingExcel}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
            >
              <Download size={16} />
              {downloadingExcel ? 'GENERANDO...' : 'EXCEL'}
            </button>
          </div>

          {/* BÚSQUEDA */}
          <div className="w-full md:w-96 relative md:ml-auto" ref={searchRef}>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-zinc-500" size={18} />
              <input
                type="search"
                placeholder="Buscar por proveedor, importe, nº factura..."
                value={ticketSearch}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => ticketSearch && setShowSuggestions(true)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
                className="w-full px-3 py-2 pl-10 pr-20 bg-zinc-900 border border-zinc-700 rounded-sm text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-amber-500 transition-colors"
              />
              <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
                {ticketSearch && (
                  <button onClick={clearSearch} className="p-1 hover:bg-zinc-800 rounded-sm transition-colors" title="Limpiar búsqueda">
                    <X size={16} className="text-zinc-500" />
                  </button>
                )}
                <button
                  onClick={startVoiceSearch}
                  disabled={isListening}
                  className={`p-1 rounded-sm transition-colors ${isListening ? 'bg-red-500 text-white animate-pulse' : 'hover:bg-zinc-800 text-zinc-500'}`}
                  title="Búsqueda por voz"
                >
                  <Mic size={16} />
                </button>
              </div>
            </div>

            {showSuggestions && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-96 overflow-y-auto z-50">
                {ticketSearch && suggestions.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800">TICKETS ENCONTRADOS</div>
                    {suggestions.map((ticket) => (
                      <div
                        key={ticket.id}
                        onClick={() => { navigate(`/share/${token}/ticket/${ticket.id}`); saveRecentSearch(ticketSearch); }}
                        className="px-3 py-2.5 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              {ticket.is_reviewed ? <span className="text-sm">✅</span> : <span className="text-sm">👁️</span>}
                              {ticket.is_foreign && <span className="text-sm">🌍</span>}
                              <StatusBadge type="ticket" value={ticket.type} />
                              {ticket.ia_warnings && <span className="text-amber-400 text-sm">⚠️</span>}
                            </div>
                            <p className="font-semibold text-sm">{ticket.provider}</p>
                            <p className="text-xs text-zinc-400 mt-0.5">{ticket.date} • Nº {ticket.invoice_number || 'N/A'}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-amber-500 font-bold text-sm">
                              {ticket.is_foreign && ticket.currency !== 'EUR' && ticket.foreign_total
                                ? `${ticket.foreign_total.toFixed(2)}${getCurrencySymbol(ticket.currency)}`
                                : `${ticket.final_total?.toFixed(2)}€`}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {ticketSearch && suggestions.length === 0 && (
                  <div className="px-4 py-6 text-center text-zinc-500"><p className="text-sm">No se encontraron tickets</p></div>
                )}
                {!ticketSearch && recentSearches.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800 flex items-center gap-2">
                      <Clock size={12} /> BÚSQUEDAS RECIENTES
                    </div>
                    {recentSearches.map((term, index) => (
                      <div
                        key={index}
                        onClick={() => { setTicketSearch(term); setShowSuggestions(true); }}
                        className="px-3 py-2 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0 flex items-center gap-2"
                      >
                        <Search size={12} className="text-zinc-600" />
                        <span className="text-sm text-zinc-300">{term}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {tickets.length > 0 && (
          <p className="text-sm text-zinc-500 mb-4">
            Mostrando {filteredTickets.length} de {tickets.length} tickets
            {ticketSearch && ` para "${ticketSearch}"`}
          </p>
        )}

        <div>
          {ticketsError && (
            <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-[12px] flex items-center gap-2 mb-3">
              Error al cargar tickets
              <button onClick={loadTickets} className="text-amber-500 hover:text-amber-400 ml-1 font-semibold">Reintentar</button>
            </div>
          )}
          {filteredTickets.length === 0 && !ticketsError ? (
            ticketSearch ? (
              <EmptyState message="No se encontraron tickets" action={{ label: "Limpiar búsqueda", onClick: clearSearch }} />
            ) : (
              <EmptyState icon={<Upload size={48} />} message="No hay tickets en este proyecto" subtitle='Haz click en "SUBIR" para comenzar' />
            )
          ) : (
            <div className="space-y-3">
              {filteredTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/share/${token}/ticket/${ticket.id}`)}
                  className={`rounded-sm p-4 cursor-pointer transition-all ${
                    ticket.provider === 'Sin proveedor' || ticket.date === 'Sin fecha'
                      ? 'bg-red-500/10 border border-red-500/30 hover:border-red-500/50 hover:shadow-lg hover:shadow-red-500/10'
                      : 'bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 hover:shadow-lg hover:shadow-amber-500/10'
                  }`}
                >
                  <div className="flex items-start gap-3 flex-wrap">
                    <div className="w-full flex items-start justify-between">
                      {/* Izquierda: emojis y badges */}
                      <div className="flex items-center gap-2 mb-5 flex-wrap">
                        {ticket.is_reviewed ? (
                          <span className="text-lg flex-shrink-0" title="Revisado">✅</span>
                        ) : (
                          <span className="text-lg flex-shrink-0" title="Pendiente revisión">👁️</span>
                        )}
                        {ticket.is_foreign && <span className="text-lg flex-shrink-0" title="Internacional">🌍</span>}
                        <StatusBadge type="ticket" value={ticket.type} />
                        {ticket.from_supplier_portal && !ticket.is_autoinvoice && (
                          <span className="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded-sm text-xs font-bold">PROVEEDOR</span>
                        )}
                        {ticket.from_supplier_portal && ticket.is_autoinvoice && (
                          <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-sm text-xs font-bold">AUTO</span>
                        )}
                        {ticket.final_total < 0 && (
                          <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-sm text-xs font-bold uppercase">ABONO</span>
                        )}
                        {(ticket.provider === 'Sin proveedor' || ticket.date === 'Sin fecha') && (
                          <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-sm text-xs font-bold uppercase">ERROR IA</span>
                        )}
                        {ticket.is_suplido && (
                          <span className="bg-zinc-700/50 text-zinc-400 border border-zinc-600/30 px-2 py-0.5 rounded-sm text-xs font-bold">SUPLIDO</span>
                        )}
                        {ticket.uploaded_by_guest_name && (
                          <span className="bg-teal-500/20 text-teal-400 border border-teal-500/30 px-2 py-0.5 rounded-sm text-xs font-bold">
                            EXTERNO — {ticket.uploaded_by_guest_name}
                          </span>
                        )}
                        {ticket.ia_warnings && (
                          <span className="text-amber-400 flex-shrink-0" title={ticket.ia_warnings}>⚠️</span>
                        )}
                      </div>

                      {/* Derecha: precio + papelera */}
                      <div className="flex items-start gap-3 flex-shrink-0">
                        <div className={`text-right ${ticket.is_suplido ? 'opacity-40' : ''}`}>
                          <p className="text-xl font-bold text-amber-500">
                            {ticket.is_foreign && ticket.currency !== 'EUR' && ticket.foreign_total
                              ? `${ticket.foreign_total.toFixed(2)}${getCurrencySymbol(ticket.currency)}`
                              : `${ticket.final_total?.toFixed(2)}€`}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {ticket.is_foreign && ticket.currency !== 'EUR'
                              ? `≈ ${ticket.final_total?.toFixed(2)}€`
                              : `Base: ${ticket.base_amount?.toFixed(2)}€`}
                          </p>
                        </div>

                        {/* Papelera con guards: cerrado → disabled; PAGADO ADMIN → disabled;
                            from_supplier_portal → oculta (el externo no gestiona facturas de proveedor) */}
                        {isClosed ? (
                          <button
                            onClick={(e) => { e.stopPropagation(); showError('El proyecto está cerrado'); }}
                            className="p-2 text-zinc-500 opacity-30 cursor-not-allowed"
                            title="Proyecto cerrado"
                          >
                            <Trash2 size={18} />
                          </button>
                        ) : ticket.payment_status === 'PAGADO ADMIN' ? (
                          <button
                            onClick={(e) => { e.stopPropagation(); showError('Factura ya pagada, no se puede eliminar'); }}
                            className="p-2 text-zinc-500 opacity-30 cursor-not-allowed"
                            title="Factura pagada — no se puede eliminar"
                          >
                            <Trash2 size={18} />
                          </button>
                        ) : ticket.from_supplier_portal ? (
                          null
                        ) : (
                          <button
                            onClick={(e) => { e.stopPropagation(); setDeleteTicketId(ticket.id); }}
                            className="p-2 hover:bg-red-500/20 text-zinc-500 hover:text-red-400 rounded-sm transition-colors"
                            title="Eliminar ticket"
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Segunda fila: nombre */}
                    <div className="w-full">
                      <h3 className="font-semibold mb-1 leading-tight">{ticket.provider}</h3>
                      <p className="text-sm text-zinc-400">{ticket.date} • Nº {ticket.invoice_number || 'N/A'}</p>
                    </div>
                  </div>

                  {/* Estados al pie */}
                  {(ticket.invoice_status || ticket.payment_status) && (
                    <div className="flex gap-2 mt-3 pt-3 border-t border-zinc-800">
                      {ticket.invoice_status && (
                        <span className="text-xs px-2 py-1 bg-zinc-800 text-zinc-400 rounded-sm">📄 {ticket.invoice_status}</span>
                      )}
                      {ticket.payment_status && (
                        <span className={`text-xs px-2 py-1 rounded-sm ${ticket.payment_status.includes('PAGADO') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                          💰 {ticket.payment_status}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <ConfirmDialog
        isOpen={!!deleteTicketId}
        onClose={() => setDeleteTicketId(null)}
        onConfirm={confirmDeleteTicket}
        title="¿Eliminar ticket?"
        message="Este ticket será eliminado permanentemente."
        confirmText="Eliminar"
        type="danger"
      />
    </div>
  );
};

export default ExternalProjectView;
