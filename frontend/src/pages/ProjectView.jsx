import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjectTickets, deleteTicket, deleteProject, closeProject, reopenProject } from '../services/api';
import { ArrowLeft, Upload, Lock, Trash2, Search, X, Mic, Clock, Unlock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { showSuccess, showError } from '../utils/toast';
import { ROLES } from '../constants/roles';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import useVoiceSearch from '../hooks/useVoiceSearch';
import useClickOutside from '../hooks/useClickOutside';

const ProjectView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reopeningProject, setReopeningProject] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingProject, setDeletingProject] = useState(false);

  // Búsqueda tickets
  const [ticketSearch, setTicketSearch] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);

  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => {
      setTicketSearch(transcript);
      const saved = localStorage.getItem(`recentSearches_project_${id}`);
      const recent = saved ? JSON.parse(saved) : [];
      const updated = [transcript, ...recent.filter(s => s !== transcript)].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem(`recentSearches_project_${id}`, JSON.stringify(updated));
    }, [id]),
  });

  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));

  useEffect(() => {
    loadProject();
    loadTickets();
    loadRecentSearches();
  }, [id]);

  const loadProject = async () => {
    try {
      const response = await getProject(id);
      setProject(response.data);
    } catch (error) {
      console.error('Error loading project:', error);
      showError('Error al cargar proyecto');
      navigate('/dashboard');
    }
  };

  const loadTickets = async () => {
    try {
      const response = await getProjectTickets(id);
      setTickets(response.data);
    } catch (error) {
      console.error('Error loading tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentSearches = () => {
    const saved = localStorage.getItem(`recentSearches_project_${id}`);
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  };

  const saveRecentSearch = (term) => {
    if (!term.trim()) return;

    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem(`recentSearches_project_${id}`, JSON.stringify(updated));
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

  const handleDeleteTicket = async (ticketId) => {
    if (!window.confirm('¿Eliminar este ticket?')) return;

    try {
      await deleteTicket(ticketId);
      showSuccess('Ticket eliminado');
      loadTickets();
      loadProject();
    } catch (error) {
      showError('Error al eliminar ticket');
    }
  };

  const handleCloseProject = () => {
    // Redirigir a pantalla de revisión antes de cerrar
    navigate(`/projects/${id}/close-review`);
  };

  const handleReopenProject = async () => {
    if (!window.confirm('¿Reabrir proyecto?')) return;

    setReopeningProject(true);
    try {
      await reopenProject(id);
      showSuccess('Proyecto reabierto correctamente');
      loadProject(); // Recargar para actualizar estado
    } catch (error) {
      showError('Error al reabrir proyecto');
    } finally {
      setReopeningProject(false);
    }
  };

  const handleDeleteProject = async () => {
    setDeletingProject(true);
    try {
      await deleteProject(id);
      showSuccess('Proyecto eliminado correctamente');
      navigate('/dashboard');
    } catch (error) {
      showError('Error al eliminar proyecto: ' + (error.response?.data?.detail || error.message));
      setDeletingProject(false);
    }
  };

  // Filtrar tickets
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

  // Sugerencias (primeros 5)
  const suggestions = filteredTickets.slice(0, 5);

  if (loading || !project) return <LoadingSpinner size="lg" fullPage />;

  // ← FIX: mayúsculas correctas (era 'admin' → siempre false)
  const isAdmin = user?.role === ROLES.ADMIN;
  const isBoss  = user?.role === ROLES.BOSS;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header OPACO Y STICKY */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver al Dashboard</span>
          </button>

          {/* MÓVIL: Layout vertical centrado */}
          <div className="flex flex-col items-center text-center md:hidden">
            {/* Código + Badge */}
            <div className="flex items-center gap-2 mb-2 flex-wrap justify-center">
              <h1 className="text-2xl font-bebas tracking-wider">{project.creative_code}</h1>
              <StatusBadge type="project" value={project.status} />
            </div>

            {/* Título */}
            <p className="text-base text-zinc-300 mb-4">{project.description}</p>

            {/* IMPORTE DESTACADO */}
            <div className="mb-3">
              <p className="text-4xl font-bold text-amber-500 mb-1">{project.total_amount?.toFixed(2)}€</p>
              <p className="text-sm text-zinc-500">{project.tickets_count} tickets</p>
            </div>

            {/* Info compacta */}
            <div className="flex items-center gap-2 text-xs text-zinc-500 flex-wrap justify-center">
              <span>{project.responsible}</span>
              <span>•</span>
              <span>{project.year}</span>
            </div>
            <p className="text-xs text-zinc-600 mt-1 truncate max-w-full px-4">
              {project.owner_company?.name || project.company || 'Sin empresa'}
            </p>
          </div>

          {/* DESKTOP: Layout horizontal original */}
          <div className="hidden md:flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bebas tracking-wider">{project.creative_code}</h1>
                <StatusBadge type="project" value={project.status} />
              </div>
              <p className="text-lg text-zinc-300 mb-1">{project.description}</p>
              <div className="flex items-center gap-4 text-sm text-zinc-500">
                <span>👤 {project.responsible}</span>
                <span>📅 {project.year}</span>
                <span>🏢 {project.owner_company?.name || project.company || 'Sin empresa'}</span>
              </div>
            </div>

            <div className="text-right">
              <p className="text-sm text-zinc-500 mb-1">IMPORTE TOTAL</p>
              <p className="text-4xl font-bold text-amber-500">{project.total_amount?.toFixed(2)}€</p>
              <p className="text-sm text-zinc-500 mt-1">{project.tickets_count} tickets</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - PADDING TOP PARA NO IR DEBAJO DEL HEADER */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-8">
        {/* Actions + Búsqueda COMPACTA */}
        <div className="flex flex-col md:flex-row md:items-center gap-3 mb-6">
          {/* Botones de acción - Ancho completo en móvil, los 3 iguales */}
          <div className="w-full md:w-auto flex gap-2">
            <button
              onClick={() => navigate(`/projects/${id}/upload`)}
              disabled={project.status === 'cerrado'}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
            >
              <Upload size={16} />
              SUBIR
            </button>

            {/* BOTÓN CERRAR (solo si EN CURSO) */}
            {project.status === 'en_curso' && (
              <button
                onClick={handleCloseProject}
                disabled={tickets.length === 0}
                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
              >
                <Lock size={16} />
                CERRAR
              </button>
            )}

            {/* BOTÓN REABRIR — visible para TODOS los roles si proyecto cerrado */}
            {project.status === 'cerrado' && (
              <button
                onClick={handleReopenProject}
                disabled={reopeningProject}
                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 font-semibold rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
              >
                <Unlock size={16} />
                {reopeningProject ? 'REABRIENDO...' : 'REABRIR'}
              </button>
            )}

            {/* BOTÓN BORRAR PROYECTO — ADMIN, BOSS, o dueño */}
            {(isAdmin || isBoss || project.owner_id === user?.id) && (
              <button
                onClick={() => setShowDeleteDialog(true)}
                disabled={deletingProject}
                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-3 bg-red-500/10 hover:bg-red-500/20 
                  text-red-400 border border-red-500/30 rounded-sm transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
              >
                <Trash2 size={16} />
                <span className="hidden sm:inline">ELIMINAR</span>
                <span className="sm:hidden">BORRAR</span>
              </button>
            )}
          </div>

          {/* BÚSQUEDA TICKETS - COMPACTA */}
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

              {/* Botones: Limpiar + Micrófono */}
              <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
                {ticketSearch && (
                  <button
                    onClick={clearSearch}
                    className="p-1 hover:bg-zinc-800 rounded-sm transition-colors"
                    title="Limpiar búsqueda"
                  >
                    <X size={16} className="text-zinc-500" />
                  </button>
                )}

                <button
                  onClick={startVoiceSearch}
                  disabled={isListening}
                  className={`p-1 rounded-sm transition-colors ${
                    isListening
                      ? 'bg-red-500 text-white animate-pulse'
                      : 'hover:bg-zinc-800 text-zinc-500'
                  }`}
                  title="Búsqueda por voz"
                >
                  <Mic size={16} />
                </button>
              </div>
            </div>

            {/* DROPDOWN: Sugerencias + Historial */}
            {showSuggestions && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-96 overflow-y-auto z-50">
                {/* Sugerencias de tickets */}
                {ticketSearch && suggestions.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800">
                      TICKETS ENCONTRADOS
                    </div>
                    {suggestions.map((ticket) => (
                      <div
                        key={ticket.id}
                        onClick={() => {
                          navigate(`/tickets/${ticket.id}/review`);
                          saveRecentSearch(ticketSearch);
                        }}
                        className="px-3 py-2.5 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              {ticket.is_reviewed ? (
                                <span className="text-sm">✅</span>
                              ) : (
                                <span className="text-sm">👁️</span>
                              )}
                              {ticket.is_foreign && (
                                <span className="text-sm">🌍</span>
                              )}
                              <StatusBadge type="ticket" value={ticket.type} />
                            </div>
                            <p className="font-semibold text-sm">{ticket.provider}</p>
                            <p className="text-xs text-zinc-400 mt-0.5">
                              {ticket.date} • Nº {ticket.invoice_number || 'N/A'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-amber-500 font-bold text-sm">{ticket.final_total?.toFixed(2)}€</p>
                            <p className="text-xs text-zinc-500">Base: {ticket.base_amount?.toFixed(2)}€</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Sin resultados */}
                {ticketSearch && suggestions.length === 0 && (
                  <div className="px-4 py-6 text-center text-zinc-500">
                    <p className="text-sm">No se encontraron tickets</p>
                  </div>
                )}

                {/* Historial de búsquedas recientes */}
                {!ticketSearch && recentSearches.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800 flex items-center gap-2">
                      <Clock size={12} />
                      BÚSQUEDAS RECIENTES
                    </div>
                    {recentSearches.map((term, index) => (
                      <div
                        key={index}
                        onClick={() => {
                          setTicketSearch(term);
                          setShowSuggestions(true);
                        }}
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

        {/* Contador resultados */}
        {tickets.length > 0 && (
          <p className="text-sm text-zinc-500 mb-4">
            Mostrando {filteredTickets.length} de {tickets.length} tickets
            {ticketSearch && ` para "${ticketSearch}"`}
          </p>
        )}

        {/* Tickets List */}
        <div>
          {filteredTickets.length === 0 ? (
            ticketSearch ? (
              <EmptyState
                message="No se encontraron tickets"
                action={{ label: "Limpiar búsqueda", onClick: clearSearch }}
              />
            ) : (
              <EmptyState
                icon={<Upload size={48} />}
                message="No hay tickets en este proyecto"
                subtitle='Haz click en "SUBIR TICKETS" para comenzar'
              />
            )
          ) : (
            <div className="space-y-3">
              {filteredTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/tickets/${ticket.id}/review`)}
                  className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-4 cursor-pointer transition-all hover:shadow-lg hover:shadow-amber-500/10"
                >
                  {/* Flex container con wrap para que nombre use todo el ancho */}
                  <div className="flex items-start gap-3 flex-wrap">
                    {/* Primera fila: Emojis + Badge | Precio + Papelera */}
                    <div className="w-full flex items-start justify-between">
                      {/* Lado izquierdo: emojis y badge */}
                      <div className="flex items-center gap-2 mb-5">
                        {ticket.is_reviewed ? (
                          <span className="text-lg flex-shrink-0" title="Revisado">✅</span>
                        ) : (
                          <span className="text-lg flex-shrink-0" title="Pendiente revisión">👁️</span>
                        )}
                        {ticket.is_foreign && (
                          <span className="text-lg flex-shrink-0" title="Internacional">🌍</span>
                        )}
                        <StatusBadge type="ticket" value={ticket.type} />
                      </div>

                      {/* Lado derecho: precio y papelera */}
                      <div className="flex items-start gap-3 flex-shrink-0">
                        <div className="text-right">
                          <p className="text-xl font-bold text-amber-500">
                            {ticket.final_total?.toFixed(2)}€
                          </p>
                          <p className="text-xs text-zinc-500">
                            Base: {ticket.base_amount?.toFixed(2)}€
                          </p>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteTicket(ticket.id);
                          }}
                          className="p-2 hover:bg-red-500/20 text-zinc-500 hover:text-red-400 rounded-sm transition-colors"
                          title="Eliminar ticket"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>

                    {/* Segunda fila: Nombre (ocupa TODO el ancho) */}
                    <div className="w-full">
                      <h3 className="font-semibold mb-1 leading-tight">{ticket.provider}</h3>
                      <p className="text-sm text-zinc-400">
                        {ticket.date} • Nº {ticket.invoice_number || 'N/A'}
                      </p>
                    </div>
                  </div>

                  {/* Estados si existen */}
                  {(ticket.invoice_status || ticket.payment_status) && (
                    <div className="flex gap-2 mt-3 pt-3 border-t border-zinc-800">
                      {ticket.invoice_status && (
                        <span className="text-xs px-2 py-1 bg-zinc-800 text-zinc-400 rounded-sm">
                          📄 {ticket.invoice_status}
                        </span>
                      )}
                      {ticket.payment_status && (
                        <span className={`text-xs px-2 py-1 rounded-sm ${
                          ticket.payment_status.includes('PAGADO')
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
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

        {/* Project Info Card */}
        <div className="mt-8 bg-zinc-900 border border-zinc-800 rounded-sm p-6">
          <h3 className="text-lg font-bebas tracking-wider mb-4">INFORMACIÓN DEL PROYECTO</h3>

          <div className="grid grid-cols-2 gap-6 text-sm">
            <div>
              <p className="text-zinc-500 mb-1">Fecha Envío Facturar</p>
              <p className="text-zinc-100">{project.send_date || 'N/A'}</p>
            </div>

            <div>
              <p className="text-zinc-500 mb-1">Tipo Factura</p>
              <p className="text-zinc-100">{project.invoice_type}</p>
            </div>

            <div>
              <p className="text-zinc-500 mb-1">Otros Datos Factura</p>
              <p className="text-zinc-100">{project.other_invoice_data || 'N/A'}</p>
            </div>

            <div>
              <p className="text-zinc-500 mb-1">OC Cliente</p>
              <p className="text-zinc-100">{project.client_oc || 'N/A'}</p>
            </div>

            <div className="col-span-2">
              <p className="text-zinc-500 mb-1">Datos Cliente</p>
              <p className="text-zinc-100 whitespace-pre-wrap">{project.client_data || 'N/A'}</p>
            </div>

            {/* ── FIX MÓVIL: Email y SharePoint en líneas separadas ── */}
            <div className="col-span-2">
              <p className="text-zinc-500 mb-1">Email Cliente</p>
              <p className="text-zinc-100 break-all">{project.client_email || 'N/A'}</p>
            </div>

            <div className="col-span-2">
              <p className="text-zinc-500 mb-1">Link Proyecto</p>
              {project.project_link ? (
                <a
                  href={project.project_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-500 hover:text-amber-400 underline break-all"
                >
                  Abrir SharePoint
                </a>
              ) : (
                <p className="text-zinc-100">N/A</p>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Modal de confirmación de borrado de proyecto */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteProject}
        title="¿Eliminar proyecto?"
        message={`Estás a punto de eliminar el proyecto "${project?.creative_code}" (${project?.description}). Esto eliminará también todos los tickets asociados (${project?.tickets_count} tickets). Esta acción no se puede deshacer.`}
        confirmText="Eliminar Proyecto"
        cancelText="Cancelar"
        type="danger"
      />
    </div>
  );
};

export default ProjectView;


