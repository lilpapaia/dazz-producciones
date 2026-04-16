import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { getTicket, updateTicket, deleteTicket, getProjectTickets, requestSupplierTicketDeletion } from '../services/api';
import { showSuccess, showError } from '../utils/toast';
import { ArrowLeft, Save, X, ZoomIn, ChevronLeft, ChevronRight, Trash2, ExternalLink } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';
import useEscapeKey from '../hooks/useEscapeKey';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatusBadge from '../components/common/StatusBadge';
import { getCurrencySymbol } from '../utils/currency';
import { useAuth } from '../context/AuthContext';
import { ROLES } from '../constants/roles';

const invoiceStatusOptions = [
  "RECIBIDO", "PEDIDO", "PENDIENTE PEDIR", "RECIBIDO PERO ERRONEO",
  "TICKET (NO FACTURA)", "A REPARTIR EN STATEMENT", "ALTA SS", "PERDIDO"
];

const paymentStatusOptions = [
  'ADELANTADO', 'PAGADO BBVA', 'PAGADO CAJA', 'PAGADO REVOLUT',
  'PAGADO SABADELL', 'PAGADO TARJETA PERSONAL', 'PAGADO VIVID',
  'PENDIENTE', 'REPARTIR STATEMENT TALENT'
];

const ReviewTicket = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Detectar si venimos desde estadísticas
  const isFromStatistics = searchParams.get('filter') === 'international';
  const projectIdFromUrl = searchParams.get('project');
  
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showLightbox, setShowLightbox] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [allTickets, setAllTickets] = useState([]);
  const [currentTicketIndex, setCurrentTicketIndex] = useState(-1);
  const [customPayment, setCustomPayment] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);

  // INT-1: Supplier ticket controls
  const { user } = useAuth();
  const isAdmin = user?.role === ROLES.ADMIN;
  const [supplierDeleteModal, setSupplierDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [requestingDelete, setRequestingDelete] = useState(false);

  // UX-L1: Detectar cambios sin guardar
  const initialTicketRef = useRef(null);
  const ticketRef = useRef(ticket);

  // UX-L2: Cerrar lightbox con Escape
  useEscapeKey(() => setShowLightbox(false), showLightbox);

  // Refs para detección de swipe
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  useEffect(() => {
    setTicket(null);
    setLoading(true);
    loadTicket();
    setCurrentPage(0);
    setCustomPayment(false);
  }, [id]);

  // Si el ticket tiene un payment_status personalizado (no está en la lista), activar modo input
  useEffect(() => {
    if (ticket?.payment_status && !paymentStatusOptions.includes(ticket.payment_status)) {
      setCustomPayment(true);
    }
  }, [ticket?.payment_status]);

  // UX-L1: Sync ticket ref for stable beforeunload listener
  useEffect(() => { ticketRef.current = ticket; }, [ticket]);

  // F-009: Compare with numeric tolerance to avoid float false-positives
  const NUMERIC_FIELDS = ['base_amount', 'iva_amount', 'irpf_amount', 'total_with_iva', 'final_total'];
  const hasUnsavedChanges = () => {
    if (!ticketRef.current || !initialTicketRef.current) return false;
    const initial = JSON.parse(initialTicketRef.current);
    const current = ticketRef.current;
    for (const key of Object.keys(current)) {
      const a = initial[key], b = current[key];
      if (NUMERIC_FIELDS.includes(key)) {
        if (Math.abs((Number(a) || 0) - (Number(b) || 0)) > 0.01) return true;
      } else {
        if (JSON.stringify(a) !== JSON.stringify(b)) return true;
      }
    }
    return false;
  };

  // UX-L1: Avisar si hay cambios sin guardar al cerrar/navegar
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges()) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Bloquear scroll cuando se abre el lightbox
  useEffect(() => {
    if (showLightbox) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    // Cleanup al desmontar
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showLightbox]);

  const loadTicket = async () => {
    try {
      // PERF-4: Launch both requests in parallel when project ID is known from URL
      const ticketPromise = getTicket(id);
      const earlyProjectTicketsPromise = projectIdFromUrl
        ? getProjectTickets(projectIdFromUrl)
        : null;

      const response = await ticketPromise;
      const currentTicket = response.data;
      setTicket(currentTicket);
      initialTicketRef.current = JSON.stringify(currentTicket);

      // Cargar todos los tickets del proyecto para navegación
      try {
        const projectTickets = earlyProjectTicketsPromise
          ? await earlyProjectTicketsPromise
          : await getProjectTickets(currentTicket.project_id);
        let ticketsToShow = projectTickets.data;
        
        // Si venimos de estadísticas, filtrar solo tickets internacionales
        if (isFromStatistics) {
          ticketsToShow = projectTickets.data.filter(t => t.is_foreign === true);
        }
        
        setAllTickets(ticketsToShow);

        // Encontrar el índice del ticket actual en la lista filtrada
        const index = ticketsToShow.findIndex(t => t.id === parseInt(id));
        setCurrentTicketIndex(index);

        // Detectar duplicado por invoice_number
        if (currentTicket.invoice_number) {
          const dup = projectTickets.data.find(t =>
            t.id !== currentTicket.id &&
            t.invoice_number === currentTicket.invoice_number
          );
          setDuplicateWarning(dup ? { ticket_id: dup.id, invoice_number: dup.invoice_number } : null);
        } else {
          setDuplicateWarning(null);
        }
      } catch (error) {
        console.error('Error loading project tickets:', error);
      }
    } catch (error) {
      showError('Error al cargar ticket');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTicket(id, {...ticket, is_reviewed: true});
      showSuccess('Ticket actualizado y marcado como revisado');
      navigate(isFromStatistics ? '/statistics' : `/projects/${ticket.project_id}`);
    } catch (error) {
      showError('Error al actualizar ticket');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteTicket(id);
      showSuccess('Ticket eliminado correctamente');
      navigate(isFromStatistics ? '/statistics' : `/projects/${ticket.project_id}`);
    } catch (error) {
      showError('Error al eliminar ticket: ' + (error.response?.data?.detail || error.message));
      setDeleting(false);
    }
  };

  // INT-1: Handle supplier ticket deletion request
  const handleRequestSupplierDeletion = async () => {
    if (!deleteReason.trim()) return;
    setRequestingDelete(true);
    try {
      await requestSupplierTicketDeletion(id, deleteReason.trim());
      showSuccess('Solicitud de borrado enviada');
      setSupplierDeleteModal(false);
      setDeleteReason('');
      navigate(`/projects/${ticket.project_id}`);
    } catch (e) {
      showError(e.response?.data?.detail || 'Error al solicitar borrado');
    } finally {
      setRequestingDelete(false);
    }
  };

  // Obtener array de páginas - VERSION SIMPLIFICADA Y ROBUSTA
  const getPages = () => {
    if (!ticket) return [];
    
    // Si file_pages existe, procesarlo
    if (ticket.file_pages) {
      // Caso 1: Ya es un array (axios lo parseó)
      if (Array.isArray(ticket.file_pages)) {
        return ticket.file_pages;
      }
      
      // Caso 2: Es un string JSON, parsearlo
      if (typeof ticket.file_pages === 'string') {
        try {
          const parsed = JSON.parse(ticket.file_pages);
          if (Array.isArray(parsed)) {
            return parsed;
          }
        } catch (e) {
          console.error('Error parseando file_pages:', e);
        }
      }
    }
    
    // Fallback: usar file_path si existe
    if (ticket.file_path && ticket.file_path.startsWith('http')) {
      return [ticket.file_path];
    }
    
    return [];
  };

  const getDownloadName = () => {
    if (!ticket?.file_name) return 'archivo';
    return ticket.file_name;
  };

  if (loading) return <LoadingSpinner size="lg" fullPage />;

  const isSupplierTicket = ticket?.from_supplier_portal === true;
  const isProjectClosed = ticket?.project_status === 'cerrado';
  const supplierFieldsDisabled = isSupplierTicket && !isAdmin;
  const isExtractionFailed = ticket?.provider === 'Sin proveedor' || ticket?.date === 'Sin fecha';
  const pages = getPages();
  const totalPages = pages.length;
  const isPdfFallback = pages.length === 1 && (pages[0].includes('/raw/') || pages[0].endsWith('.pdf'));
  
  // Detectar swipe en móvil para cambiar de foto
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e) => {
    touchEndX.current = e.changedTouches[0].clientX;
    handleSwipe();
  };

  const handleSwipe = () => {
    const swipeThreshold = 50; // mínimo 50px para considerar swipe
    const diff = touchStartX.current - touchEndX.current;

    if (Math.abs(diff) > swipeThreshold) {
      if (diff > 0 && currentPage < totalPages - 1) {
        // Swipe izquierda → siguiente foto
        setCurrentPage(p => p + 1);
      } else if (diff < 0 && currentPage > 0) {
        // Swipe derecha → foto anterior
        setCurrentPage(p => p - 1);
      }
    }
  };

  // Funciones de navegación entre tickets
  const hasPrevTicket = currentTicketIndex > 0;
  const hasNextTicket = currentTicketIndex >= 0 && currentTicketIndex < allTickets.length - 1;

  const goToPrevTicket = () => {
    if (hasPrevTicket) {
      const prevTicket = allTickets[currentTicketIndex - 1];
      const url = isFromStatistics 
        ? `/tickets/${prevTicket.id}/review?filter=international&project=${ticket.project_id}`
        : `/tickets/${prevTicket.id}/review`;
      navigate(url);
    }
  };

  const goToNextTicket = () => {
    if (hasNextTicket) {
      const nextTicket = allTickets[currentTicketIndex + 1];
      const url = isFromStatistics 
        ? `/tickets/${nextTicket.id}/review?filter=international&project=${ticket.project_id}`
        : `/tickets/${nextTicket.id}/review`;
      navigate(url);
    }
  };

  // Función para truncar nombre de archivo inteligentemente
  const getTruncatedFileName = (fileName) => {
    if (!fileName) return 'archivo';
    
    const maxLength = 20;
    if (fileName.length <= maxLength) return fileName;
    
    // Primeros 12 + "..." + últimos 8
    return `${fileName.slice(0, 12)}...${fileName.slice(-8)}`;
  };

  // Handler para doble click en zonas laterales
  const handleLateralDoubleClick = (side) => {
    if (side === 'left' && hasPrevTicket) {
      goToPrevTicket();
    } else if (side === 'right' && hasNextTicket) {
      goToNextTicket();
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button 
            onClick={() => navigate(isFromStatistics ? '/statistics' : `/projects/${ticket.project_id}`)} 
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">{isFromStatistics ? 'Volver a Estadísticas' : 'Volver al Proyecto'}</span>
          </button>
          
          {/* Título con separador y emoji */}
          <div className="flex items-center gap-3 mb-3">
            <h1 className="text-3xl font-bebas tracking-wider">REVISAR TICKET</h1>
            <span className="text-zinc-600 text-2xl">|</span>
            {ticket.is_reviewed ? <span className="text-2xl">✅</span> : <span className="text-2xl">👁️</span>}
          </div>

          {/* Badges en su propia fila */}
          <div className="flex items-center gap-2 mb-3">
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
            {ticket.is_foreign && (
              <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-sm text-xs font-bold uppercase border border-blue-500/30 flex items-center gap-1">
                🌍 INTERNACIONAL
              </span>
            )}
          </div>

          {/* Fila: Contador izquierda + Eliminar derecha */}
          <div className="flex items-center justify-between">
            {/* Contador de tickets - IZQUIERDA */}
            {allTickets.length > 1 && currentTicketIndex >= 0 ? (
              <span className="inline-flex items-center px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-sm text-xs font-mono text-amber-400">
                Ticket {currentTicketIndex + 1}/{allTickets.length}
              </span>
            ) : (
              <div></div>
            )}

            {/* Botón Eliminar/Gestionar - DERECHA - Responsive */}
            {isProjectClosed ? (
              <button
                onClick={() => showError('Reabre el proyecto para poder eliminar tickets')}
                className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 text-zinc-600 border border-zinc-700 rounded-sm opacity-30 cursor-not-allowed"
                title="Proyecto cerrado — reabre para eliminar"
              >
                <Trash2 size={18} />
                <span className="hidden md:inline text-sm font-semibold">Cerrado</span>
              </button>
            ) : ticket.payment_status === 'PAGADO ADMIN' ? (
              <button
                disabled
                className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 text-zinc-600 border border-zinc-700 rounded-sm opacity-30 cursor-not-allowed"
                title="Factura pagada — no se puede eliminar"
              >
                <Trash2 size={18} />
                <span className="hidden md:inline text-sm font-semibold">Pagada</span>
              </button>
            ) : !isSupplierTicket ? (
              <button
                onClick={() => setShowDeleteDialog(true)}
                disabled={deleting}
                className="flex items-center gap-2 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Eliminar ticket"
              >
                <Trash2 size={18} />
                <span className="hidden md:inline text-sm font-semibold">Eliminar</span>
              </button>
            ) : isAdmin ? (
              <button
                onClick={() => navigate(`/suppliers/invoices/${ticket.supplier_invoice_id}`)}
                className="flex items-center gap-2 px-3 py-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-sm transition-colors"
                title="Gestionar en proveedores"
              >
                <ExternalLink size={18} />
                <span className="hidden md:inline text-sm font-semibold">Proveedores</span>
              </button>
            ) : (
              <button
                onClick={() => { setSupplierDeleteModal(true); setDeleteReason(''); }}
                className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-sm transition-colors"
                title="Solicitar borrado"
              >
                <Trash2 size={18} />
                <span className="hidden md:inline text-sm font-semibold">Solicitar borrado</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-6 pb-8 relative">
        {/* Zonas laterales para doble click - SIN hover visible para no confundir */}
        {hasPrevTicket && (
          <div 
            onDoubleClick={() => handleLateralDoubleClick('left')}
            className="fixed left-0 top-0 bottom-0 w-10 z-30 cursor-pointer"
            title="Doble click para ticket anterior"
          />
        )}
        {hasNextTicket && (
          <div 
            onDoubleClick={() => handleLateralDoubleClick('right')}
            className="fixed right-0 top-0 bottom-0 w-10 z-30 cursor-pointer"
            title="Doble click para siguiente ticket"
          />
        )}

        {/* Flechas flotantes de navegación - SOLO DESKTOP */}
        {hasPrevTicket && (
          <button
            onClick={goToPrevTicket}
            className="hidden md:flex fixed left-4 top-1/2 -translate-y-1/2 z-40 bg-zinc-800/90 hover:bg-zinc-700 text-zinc-300 hover:text-white p-3 rounded-full border border-zinc-600 items-center justify-center transition-all shadow-lg"
            title="Ticket anterior"
          >
            <ChevronLeft size={24} />
          </button>
        )}
        {hasNextTicket && (
          <button
            onClick={goToNextTicket}
            className="hidden md:flex fixed right-4 top-1/2 -translate-y-1/2 z-40 bg-zinc-800/90 hover:bg-zinc-700 text-zinc-300 hover:text-white p-3 rounded-full border border-zinc-600 items-center justify-center transition-all shadow-lg"
            title="Siguiente ticket"
          >
            <ChevronRight size={24} />
          </button>
        )}

        {duplicateWarning && (
          <div className="mb-4 bg-amber-500/10 border-2 border-amber-500/40 rounded-sm p-4 flex items-center justify-between gap-4">
            <p className="text-sm text-amber-300">
              Ya existe un ticket con el n.o de factura <span className="font-bold">{duplicateWarning.invoice_number}</span> (ticket #{duplicateWarning.ticket_id}). Revisa si es un duplicado antes de guardar.
            </p>
            <button
              onClick={() => navigate(`/tickets/${duplicateWarning.ticket_id}`)}
              className="flex-shrink-0 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/40 rounded-sm text-xs font-bold transition-colors"
            >
              Ver ticket original
            </button>
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 space-y-6">

          {/* VISOR GALERÍA */}
          {pages.length > 0 && (
            <div className="bg-zinc-950 border border-zinc-700 rounded-sm overflow-hidden">
              
              {/* Imagen principal o PDF iframe */}
              {isPdfFallback ? (
                <iframe
                  src={pages[0]}
                  title="PDF"
                  className="w-full h-96 bg-zinc-900"
                />
              ) : (
                <div
                  className="relative cursor-zoom-in group"
                  onClick={() => setShowLightbox(true)}
                >
                  <img
                    src={pages[currentPage]}
                    alt={`Página ${currentPage + 1}`}
                    className="w-full max-h-96 object-contain bg-zinc-900"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="bg-amber-500 text-zinc-950 p-3 rounded-full shadow-lg">
                        <ZoomIn size={24} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Controles navegación - DEBAJO de la imagen, centrado */}
              <div className="px-4 py-3 bg-zinc-900/80 border-t border-zinc-800 flex items-center justify-center">
                <div className="flex items-center gap-3">
                  {/* Flecha izquierda - SIEMPRE visible */}
                  <button
                    onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                    disabled={currentPage === 0 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                  >
                    <ChevronLeft size={18} />
                  </button>

                  {/* Nombre del archivo - truncado inteligentemente */}
                  <span className="text-sm font-mono text-zinc-300 text-center">
                    {totalPages > 1 
                      ? `${currentPage + 1}/${totalPages} - ${getTruncatedFileName(ticket.file_name)}` 
                      : getTruncatedFileName(ticket.file_name)
                    }
                  </span>

                  {/* Flecha derecha - SIEMPRE visible */}
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={currentPage === totalPages - 1 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>

              {/* Dots indicadores (solo si hay más de 1 página) */}
              {totalPages > 1 && (
                <div className="px-4 pb-3 bg-zinc-900/80 flex justify-center gap-1.5">
                  {pages.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setCurrentPage(i)}
                      className={`w-2 h-2 rounded-full transition-colors ${i === currentPage ? 'bg-amber-500' : 'bg-zinc-600 hover:bg-zinc-400'}`}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* LIGHTBOX */}
          {showLightbox && pages.length > 0 && !isPdfFallback && (
            <div
              className="fixed inset-0 !m-0 bg-black z-50 flex items-center justify-center"
              style={{
                minHeight: '100dvh',
                paddingTop: 'env(safe-area-inset-top, 0px)',
                paddingBottom: 'env(safe-area-inset-bottom, 0px)'
              }}
              onClick={() => setShowLightbox(false)}
            >
              <button
                onClick={(e) => { e.stopPropagation(); setShowLightbox(false); }}
                className="absolute top-4 right-4 text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700 z-10"
                style={{ marginTop: 'env(safe-area-inset-top, 0px)' }}
              >
                <X size={32} />
              </button>

              {/* Flecha izquierda lightbox - SOLO DESKTOP */}
              {totalPages > 1 && currentPage > 0 && (
                <button
                  onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p - 1); }}
                  className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center"
                >
                  <ChevronLeft size={28} />
                </button>
              )}

              <img
                src={pages[currentPage]}
                alt={`Página ${currentPage + 1}`}
                className="max-w-full max-h-[90vh] object-contain shadow-2xl select-none"
                onClick={(e) => e.stopPropagation()}
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
              />

              {/* Flecha derecha lightbox - SOLO DESKTOP */}
              {totalPages > 1 && currentPage < totalPages - 1 && (
                <button
                  onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p + 1); }}
                  className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700 items-center justify-center"
                >
                  <ChevronRight size={28} />
                </button>
              )}

              {/* Contador de páginas - Abajo centro */}
              {totalPages > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-900/80 px-4 py-2 rounded-full text-sm font-mono text-zinc-300 border border-zinc-700">
                  Página {currentPage + 1} / {totalPages}
                </div>
              )}
            </div>
          )}

          {/* Alerta IA - Solo en desktop */}
          <div className={`hidden md:block rounded-sm p-4 ${
            isExtractionFailed ? 'bg-red-500/10 border border-red-500/30'
            : ticket.ia_warnings ? 'bg-amber-500/10 border border-amber-500/30'
            : 'bg-blue-500/10 border border-blue-500/30'
          }`}>
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 ${
                isExtractionFailed ? 'text-red-400'
                : ticket.ia_warnings ? 'text-amber-400'
                : 'text-blue-400'
              }`}>
                {isExtractionFailed || ticket.ia_warnings ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div>
                <p className={`text-sm font-semibold ${
                  isExtractionFailed ? 'text-red-400'
                  : ticket.ia_warnings ? 'text-amber-400'
                  : 'text-blue-400'
                }`}>
                  {isExtractionFailed ? 'Error en extracción IA' : ticket.ia_warnings ? 'Warnings en extracción IA' : 'Datos extraídos por IA'}
                </p>
                <p className="text-xs text-zinc-400 mt-1">Revisa la información y corrige si es necesario</p>
                {ticket.ia_warnings && (
                  <div className="mt-2 space-y-0.5">
                    {ticket.ia_warnings.split('\n').map((w, i) => (
                      <div key={i} className={`text-xs font-mono ${isExtractionFailed ? 'text-red-300/80' : 'text-amber-300/80'}`}>• {w}</div>
                    ))}
                  </div>
                )}
                {isExtractionFailed && (
                  <p className="text-xs text-red-400 mt-2 font-semibold">Completa los datos manualmente para poder revisar este ticket.</p>
                )}
              </div>
            </div>
          </div>

          {/* INT-1: Banner ticket proveedor */}
          {isSupplierTicket && (
            <div className="bg-purple-500/10 border-2 border-purple-500/30 rounded-sm p-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔗</span>
                  <p className="text-sm text-purple-300">
                    Esta factura proviene del portal de proveedores. Los importes no son editables.
                  </p>
                </div>
                {isAdmin && ticket.supplier_invoice_id && (
                  <button
                    onClick={() => navigate(`/suppliers/invoices/${ticket.supplier_invoice_id}`)}
                    className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/40 rounded-sm text-xs font-bold transition-colors"
                  >
                    <ExternalLink size={14} />
                    Gestionar en proveedores
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Info Internacional */}
          {ticket.is_foreign && (
            <div className="bg-blue-500/10 border-2 border-blue-500/30 rounded-sm p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">🌍</span>
                <h3 className="text-lg font-bold text-blue-400">FACTURA INTERNACIONAL</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-zinc-500 text-xs mb-1">País</p>
                  <p className="font-semibold">{ticket.country_code || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-zinc-500 text-xs mb-1">Divisa</p>
                  <p className="font-semibold">
                    <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-sm">
                      {getCurrencySymbol(ticket.currency)} {ticket.currency}
                    </span>
                  </p>
                </div>
                <div>
                  <p className="text-zinc-500 text-xs mb-1">Clasificación</p>
                  <span className={`px-2 py-1 rounded text-xs ${ticket.geo_classification === 'UE' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}>
                    {ticket.geo_classification || 'N/A'}
                  </span>
                </div>
                {ticket.exchange_rate && (
                  <div>
                    <p className="text-zinc-500 text-xs mb-1">Tasa cambio</p>
                    <p className="font-semibold">{ticket.exchange_rate.toFixed(4)}</p>
                  </div>
                )}
              </div>
              {ticket.foreign_amount && (
                <div className="mt-4 pt-4 border-t border-blue-500/30">
                  <p className="text-xs text-zinc-500 mb-3">Importes en divisa original:</p>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <div>
                      <span className="text-zinc-400 text-xs">Base: </span>
                      <span className="font-semibold text-blue-400">
                        {getCurrencySymbol(ticket.currency)}{ticket.foreign_amount.toFixed(2)}
                      </span>
                    </div>
                    {ticket.foreign_tax_amount && (
                      <>
                        <span className="text-zinc-600">|</span>
                        <div>
                          <span className="text-zinc-400 text-xs">IVA: </span>
                          <span className="font-semibold text-blue-400">
                            {getCurrencySymbol(ticket.currency)}{ticket.foreign_tax_amount.toFixed(2)}
                          </span>
                        </div>
                      </>
                    )}
                    {ticket.foreign_tax_eur && (
                      <>
                        <span className="text-zinc-600">|</span>
                        <div>
                          <span className="text-zinc-400 text-xs">IVA reclamable: </span>
                          <span className="font-bold text-green-400">{ticket.foreign_tax_eur.toFixed(2)}€ ✅</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Fecha y Nº Factura en misma línea */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">FECHA FACTURA</label>
              <input type="text" value={ticket.date || ''} onChange={(e) => setTicket({...ticket, date: e.target.value})}
                disabled={isSupplierTicket}
                placeholder="DD/MM/AAAA" className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
            </div>
            {ticket.type === 'factura' && (
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">Nº FACTURA</label>
                <input type="text" value={ticket.invoice_number || ''} onChange={(e) => setTicket({...ticket, invoice_number: e.target.value})}
                  disabled={isSupplierTicket}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
              </div>
            )}
          </div>

          {/* Proveedor solo */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">PROVEEDOR *</label>
            <input type="text" value={ticket.provider || ''} onChange={(e) => setTicket({...ticket, provider: e.target.value})}
              disabled={isSupplierTicket}
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
          </div>

          {/* Teléfono y Email juntos - SIN GAP */}
          {ticket.type === 'factura' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">TELÉFONO</label>
                <input type="text" value={ticket.phone || ''} onChange={(e) => setTicket({...ticket, phone: e.target.value})}
                  disabled={isSupplierTicket}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
                <input type="email" value={ticket.email || ''} onChange={(e) => setTicket({...ticket, email: e.target.value})}
                  disabled={isSupplierTicket}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
              </div>
            </div>
          )}

          {ticket.type === 'factura' && (
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOMBRE CONTACTO</label>
              <input type="text" value={ticket.contact_name || ''} onChange={(e) => setTicket({...ticket, contact_name: e.target.value})}
                disabled={isSupplierTicket}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 disabled:opacity-60 disabled:cursor-not-allowed" />
            </div>
          )}

          {/* Desglose importes */}
          <div className="bg-zinc-950 border border-zinc-700 rounded-sm p-4">
            {ticket.is_foreign && ticket.currency !== 'EUR' ? (
              <>
                {/* ═══ INTERNATIONAL: Dual currency — Parallel columns ═══ */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-zinc-500 font-mono tracking-wider">DESGLOSE IMPORTES</p>
                    <span className="bg-amber-500/15 text-amber-400 text-[11px] font-bold px-2 py-0.5 rounded">{ticket.currency}</span>
                  </div>
                  {ticket.exchange_rate && (
                    <span className="text-[10px] text-zinc-600 font-mono bg-zinc-800 px-2.5 py-1 rounded">1 {ticket.currency} = {ticket.exchange_rate.toFixed(4)} EUR</span>
                  )}
                </div>

                {(() => {
                  const rate = ticket.exchange_rate || 1;
                  const sym = getCurrencySymbol(ticket.currency);
                  const inputCls = `w-full bg-zinc-800 border border-zinc-700 rounded-sm px-3 py-2 text-zinc-100 font-semibold focus:outline-none focus:border-amber-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none${isSupplierTicket ? ' opacity-60 cursor-not-allowed' : ''}`;

                  const updateFromForeign = (foreignBase, ivaPct) => {
                    const foreignTax = Math.round(foreignBase * ivaPct * 100) / 100;
                    const foreignTotal = Math.round((foreignBase + foreignTax) * 100) / 100;
                    setTicket({
                      ...ticket,
                      foreign_amount: foreignBase,
                      foreign_tax_amount: foreignTax,
                      foreign_total: foreignTotal,
                      foreign_tax_eur: Math.round(foreignTax * rate * 100) / 100,
                      iva_percentage: ivaPct,
                      base_amount: Math.round(foreignBase * rate * 100) / 100,
                      iva_amount: Math.round(foreignTax * rate * 100) / 100,
                      total_with_iva: Math.round(foreignTotal * rate * 100) / 100,
                      final_total: Math.round(foreignTotal * rate * 100) / 100,
                    });
                  };

                  return (
                    <>
                      {/* ── Desktop: grid compartido para alinear filas ── */}
                      <div className="hidden md:grid grid-cols-[1fr_1px_1fr] gap-0">
                        {/* Headers */}
                        <p className="text-[10px] text-zinc-600 font-mono tracking-wider uppercase pb-3 pr-5">Divisa original ({ticket.currency})</p>
                        <div className="bg-zinc-800" />
                        <p className="text-[10px] text-zinc-600 font-mono tracking-wider uppercase pb-3 pl-5">Equivalencia EUR</p>

                        {/* Base row */}
                        <div className="flex items-center justify-between py-2.5 border-b border-zinc-800/50 pr-5">
                          <label className="text-[13px] text-zinc-400">Base</label>
                          <div className="relative w-28">
                            <input type="number" step="0.01"
                              value={ticket.foreign_amount ?? ''}
                              onChange={(e) => updateFromForeign(parseFloat(e.target.value) || 0, ticket.iva_percentage || 0)}
                              disabled={isSupplierTicket}
                              className={`${inputCls} text-right pr-7 text-sm`} />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-xs pointer-events-none">{sym}</span>
                          </div>
                        </div>
                        <div className="bg-zinc-800 border-b border-zinc-800/50" />
                        <div className="flex items-center justify-between py-2.5 border-b border-zinc-800/50 pl-5">
                          <label className="text-[13px] text-zinc-500">Base</label>
                          <span className="text-sm text-zinc-400 font-mono">≈ {ticket.base_amount?.toFixed(2)} €</span>
                        </div>

                        {/* IVA row */}
                        <div className="flex items-center justify-between py-2.5 border-b border-zinc-800/50 pr-5">
                          <label className="text-[13px] text-zinc-400">IVA</label>
                          <div className="flex items-center gap-2">
                            <div className="relative w-16">
                              <input type="number" step="1" min="0" max="100"
                                value={ticket.iva_percentage != null ? Math.round(ticket.iva_percentage * 100) : ''}
                                onChange={(e) => updateFromForeign(ticket.foreign_amount || 0, (parseFloat(e.target.value) || 0) / 100)}
                                disabled={isSupplierTicket}
                                className={`${inputCls} text-center pr-6 text-sm`} />
                              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 text-xs pointer-events-none">%</span>
                            </div>
                            <span className="text-sm text-zinc-300 font-mono w-20 text-right">{ticket.foreign_tax_amount?.toFixed(2)}{sym}</span>
                          </div>
                        </div>
                        <div className="bg-zinc-800 border-b border-zinc-800/50" />
                        <div className="flex items-center justify-between py-2.5 border-b border-zinc-800/50 pl-5">
                          <label className="text-[13px] text-zinc-500">IVA</label>
                          <span className="text-sm text-zinc-400 font-mono">≈ {ticket.iva_amount?.toFixed(2)} €</span>
                        </div>

                        {/* Total row */}
                        <div className="flex items-center justify-between pt-3 pr-5">
                          <span className="text-[13px] text-zinc-300 font-medium">Total</span>
                          <span className="text-xl font-bold text-amber-500 font-mono">{ticket.foreign_total?.toFixed(2)} {sym}</span>
                        </div>
                        <div className="bg-zinc-800" />
                        <div className="flex items-center justify-between pt-3 pl-5">
                          <span className="text-[13px] text-zinc-500">Total</span>
                          <span className="text-lg text-zinc-300 font-medium font-mono">≈ {ticket.final_total?.toFixed(2)} €</span>
                        </div>
                      </div>

                      {/* ── Móvil: apilado ── */}
                      <div className="md:hidden space-y-4">
                        {/* Divisa original */}
                        <div>
                          <p className="text-[10px] text-zinc-600 font-mono tracking-wider uppercase mb-3">Divisa original ({ticket.currency})</p>
                          <div className="flex items-center justify-between py-2 border-b border-zinc-800/50">
                            <label className="text-[13px] text-zinc-400">Base</label>
                            <div className="relative w-28">
                              <input type="number" step="0.01"
                                value={ticket.foreign_amount ?? ''}
                                onChange={(e) => updateFromForeign(parseFloat(e.target.value) || 0, ticket.iva_percentage || 0)}
                                disabled={isSupplierTicket}
                                className={`${inputCls} text-right pr-7 text-sm`} />
                              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-xs pointer-events-none">{sym}</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between py-2 border-b border-zinc-800/50">
                            <label className="text-[13px] text-zinc-400">IVA</label>
                            <div className="flex items-center gap-2">
                              <div className="relative w-16">
                                <input type="number" step="1" min="0" max="100"
                                  value={ticket.iva_percentage != null ? Math.round(ticket.iva_percentage * 100) : ''}
                                  onChange={(e) => updateFromForeign(ticket.foreign_amount || 0, (parseFloat(e.target.value) || 0) / 100)}
                                  disabled={isSupplierTicket}
                                  className={`${inputCls} text-center pr-6 text-sm`} />
                                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 text-xs pointer-events-none">%</span>
                              </div>
                              <span className="text-sm text-zinc-300 font-mono w-20 text-right">{ticket.foreign_tax_amount?.toFixed(2)}{sym}</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between pt-3">
                            <span className="text-[13px] text-zinc-300 font-medium">Total</span>
                            <span className="text-xl font-bold text-amber-500 font-mono">{ticket.foreign_total?.toFixed(2)} {sym}</span>
                          </div>
                        </div>

                        {/* Equivalencia EUR */}
                        <div className="border-t border-zinc-700 pt-4">
                          <p className="text-[10px] text-zinc-600 font-mono tracking-wider uppercase mb-3">Equivalencia EUR</p>
                          <div className="flex items-center justify-between py-1.5">
                            <span className="text-[13px] text-zinc-500">Base</span>
                            <span className="text-sm text-zinc-400 font-mono">≈ {ticket.base_amount?.toFixed(2)} €</span>
                          </div>
                          <div className="flex items-center justify-between py-1.5">
                            <span className="text-[13px] text-zinc-500">IVA</span>
                            <span className="text-sm text-zinc-400 font-mono">≈ {ticket.iva_amount?.toFixed(2)} €</span>
                          </div>
                          <div className="flex items-center justify-between pt-2 mt-1 border-t border-zinc-800/50">
                            <span className="text-[13px] text-zinc-400">Total</span>
                            <span className="text-lg text-zinc-300 font-medium font-mono">≈ {ticket.final_total?.toFixed(2)} €</span>
                          </div>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </>
            ) : (
              <>
                {/* ═══ NATIONAL: EUR only ═══ */}
                <p className="text-xs text-zinc-500 font-mono mb-3 tracking-wider">DESGLOSE IMPORTES</p>

                <div className="flex items-end gap-4 mb-4">
                  <div className="flex-1">
                    <label className="block text-zinc-400 mb-1 text-xs">Base</label>
                    <div className="relative">
                      <input type="number" step="0.01"
                        value={ticket.base_amount ?? ''}
                        onChange={(e) => {
                          const base = parseFloat(e.target.value) || 0;
                          const ivaP = ticket.iva_percentage || 0;
                          const irpfP = ticket.irpf_percentage || 0;
                          const iva = Math.round(base * ivaP * 100) / 100;
                          const irpf = Math.round(base * irpfP * 100) / 100;
                          setTicket({ ...ticket, base_amount: base, iva_amount: iva, irpf_amount: irpf, total_with_iva: Math.round((base + iva) * 100) / 100, final_total: Math.round((base + iva - irpf) * 100) / 100 });
                        }}
                        disabled={isSupplierTicket}
                        className={`w-full bg-zinc-800 border border-zinc-700 rounded-sm px-3 py-2 text-zinc-100 font-semibold focus:outline-none focus:border-amber-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none${isSupplierTicket ? ' opacity-60 cursor-not-allowed' : ''}`}
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-sm pointer-events-none">€</span>
                    </div>
                  </div>
                  <div className="w-20">
                    <label className="block text-zinc-400 mb-1 text-xs">% IVA</label>
                    <div className="relative">
                      <input type="number" step="1" min="0" max="100"
                        value={ticket.iva_percentage != null ? Math.round(ticket.iva_percentage * 100) : ''}
                        onChange={(e) => {
                          const pct = (parseFloat(e.target.value) || 0) / 100;
                          const base = ticket.base_amount || 0;
                          const irpf = ticket.irpf_amount || 0;
                          const iva = Math.round(base * pct * 100) / 100;
                          setTicket({ ...ticket, iva_percentage: pct, iva_amount: iva, total_with_iva: Math.round((base + iva) * 100) / 100, final_total: Math.round((base + iva - irpf) * 100) / 100 });
                        }}
                        disabled={isSupplierTicket}
                        className={`w-full bg-zinc-800 border border-zinc-700 rounded-sm px-3 py-2 pr-7 text-zinc-100 font-semibold focus:outline-none focus:border-amber-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none${isSupplierTicket ? ' opacity-60 cursor-not-allowed' : ''}`}
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-sm pointer-events-none">%</span>
                    </div>
                  </div>
                  <div className="w-20">
                    <label className="block text-zinc-400 mb-1 text-xs">% IRPF</label>
                    <div className="relative">
                      <select
                        value={ticket.irpf_percentage != null ? Math.round(ticket.irpf_percentage * 100) : 0}
                        onChange={(e) => {
                          const pct = (parseFloat(e.target.value) || 0) / 100;
                          const base = ticket.base_amount || 0;
                          const iva = ticket.iva_amount || 0;
                          const irpf = Math.round(base * pct * 100) / 100;
                          setTicket({ ...ticket, irpf_percentage: pct, irpf_amount: irpf, final_total: Math.round((base + iva - irpf) * 100) / 100 });
                        }}
                        disabled={isSupplierTicket}
                        className={`w-full bg-zinc-800 border border-zinc-700 rounded-sm px-3 py-2 text-zinc-100 font-semibold focus:outline-none focus:border-amber-500${isSupplierTicket ? ' opacity-60 cursor-not-allowed' : ''}`}
                      >
                        <option value="0">0%</option>
                        <option value="7">7%</option>
                        <option value="15">15%</option>
                        <option value="19">19%</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex-1">
                    <label className="block text-zinc-400 mb-1 text-xs">IVA</label>
                    <p className="px-3 py-2 font-semibold text-zinc-300">{ticket.iva_amount?.toFixed(2)}€</p>
                  </div>
                </div>

                {(ticket.irpf_amount > 0) && (
                  <div className="mb-2 text-xs text-zinc-500">
                    IRPF: -{ticket.irpf_amount?.toFixed(2)}€
                  </div>
                )}

                <div className="pt-3 border-t border-zinc-700">
                  <p className="text-zinc-400 mb-1 text-xs">Total</p>
                  <p className="text-xl font-bold text-amber-500">{ticket.final_total?.toFixed(2)}€</p>
                </div>
              </>
            )}
          </div>

          {/* Notas */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">DESCRIPCIÓN</label>
            <textarea value={ticket.notes || ''} onChange={(e) => setTicket({...ticket, notes: e.target.value})}
              rows={3} placeholder="Descripción del gasto, observaciones..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 resize-none" />
          </div>

          {/* Gasto suplido — solo tickets internos (no proveedor) */}
          {!ticket.from_supplier_portal && (
            <label className="flex items-center gap-3 cursor-pointer group">
              <input type="checkbox" checked={ticket.is_suplido || false}
                onChange={(e) => setTicket({...ticket, is_suplido: e.target.checked})}
                className="w-4 h-4 rounded border-zinc-600 bg-zinc-950 text-amber-500 focus:ring-amber-500 focus:ring-offset-0 cursor-pointer" />
              <div>
                <span className="text-sm text-zinc-300 group-hover:text-zinc-100 transition-colors">Gasto suplido</span>
                <p className="text-[11px] text-zinc-600">Su importe ya está incluido en otra factura del proyecto. No suma al total.</p>
              </div>
            </label>
          )}

          {/* Estados */}
          <div className={customPayment ? "flex flex-col gap-4" : "grid grid-cols-2 gap-4"}>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS FACTURA</label>
              <select value={ticket.invoice_status || ''} onChange={(e) => setTicket({...ticket, invoice_status: e.target.value})}
                disabled={supplierFieldsDisabled}
                className={`w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500${supplierFieldsDisabled ? ' opacity-60 cursor-not-allowed' : ''}`}>
                <option value="">Seleccionar...</option>
                {invoiceStatusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS PAGO</label>
              {!customPayment ? (
                <select
                  value={paymentStatusOptions.includes(ticket.payment_status) ? ticket.payment_status : (ticket.payment_status ? '__custom__' : '')}
                  disabled={supplierFieldsDisabled}
                  onChange={(e) => {
                    if (e.target.value === '__custom__') {
                      setCustomPayment(true);
                      setTicket({...ticket, payment_status: ''});
                    } else {
                      setTicket({...ticket, payment_status: e.target.value});
                    }
                  }}
                  className={`w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500${supplierFieldsDisabled ? ' opacity-60 cursor-not-allowed' : ''}`}
                >
                  <option value="">Seleccionar...</option>
                  {paymentStatusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                  <option value="__custom__">✏️ Escribir otro...</option>
                </select>
              ) : (
                <div className="flex gap-2 items-center">
                  <input
                    type="text"
                    autoFocus
                    disabled={supplierFieldsDisabled}
                    value={ticket.payment_status || ''}
                    onChange={(e) => setTicket({...ticket, payment_status: e.target.value})}
                    onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault(); }}
                    placeholder="Escribe el estatus de pago..."
                    className={`flex-1 min-w-0 bg-zinc-950 border border-amber-500 rounded-sm px-3 py-2.5 text-zinc-100 focus:outline-none text-sm${supplierFieldsDisabled ? ' opacity-60 cursor-not-allowed' : ''}`}
                  />
                  <button
                    onClick={() => { setCustomPayment(false); setTicket({...ticket, payment_status: ''}); }}
                    className="flex-shrink-0 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-100 rounded-sm transition-colors text-sm"
                    title="Volver al desplegable"
                  >
                    ↩
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <button 
              onClick={() => navigate(isFromStatistics ? '/statistics' : `/projects/${ticket.project_id}`)} 
              className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
            >
              Cancelar
            </button>
            <button onClick={handleSave} disabled={saving}
              className="flex-1 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2">
              <Save size={18} />
              {saving ? 'GUARDANDO...' : 'REVISADO ✓'}
            </button>
          </div>

        </div>
      </main>

      {/* Modal de confirmación de borrado (tickets internos) */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="¿Eliminar ticket?"
        message={`Estás a punto de eliminar el ticket "${ticket?.file_name}". Esta acción no se puede deshacer.`}
        confirmText="Eliminar"
        cancelText="Cancelar"
        type="danger"
      />

      {/* INT-1: Modal solicitud borrado ticket proveedor */}
      {supplierDeleteModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4" onClick={() => setSupplierDeleteModal(false)}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-zinc-800">
              <h3 className="text-lg font-bold text-zinc-100">Solicitar borrado</h3>
              <button onClick={() => setSupplierDeleteModal(false)} className="text-zinc-400 hover:text-zinc-100 transition-colors p-1">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <p className="text-zinc-300 text-sm mb-1">
                <span className="font-semibold">{ticket?.provider}</span> — {ticket?.final_total?.toFixed(2)}€
              </p>
              <p className="text-zinc-500 text-xs mb-4">
                Esta factura viene del portal de proveedores. Se enviara una solicitud de borrado al administrador.
              </p>
              <textarea
                value={deleteReason}
                onChange={e => setDeleteReason(e.target.value)}
                placeholder="Motivo de la solicitud..."
                rows={3}
                className="w-full bg-zinc-950 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-sm focus:border-amber-500 outline-none resize-none"
              />
            </div>
            <div className="flex gap-3 p-6 border-t border-zinc-800">
              <button onClick={() => setSupplierDeleteModal(false)}
                className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold">
                Cancelar
              </button>
              <button
                onClick={handleRequestSupplierDeletion}
                disabled={!deleteReason.trim() || requestingDelete}
                className="flex-1 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 rounded-sm transition-colors font-bold disabled:opacity-50 disabled:cursor-not-allowed">
                {requestingDelete ? 'Enviando...' : 'Solicitar borrado'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewTicket;
