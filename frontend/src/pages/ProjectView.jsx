import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjectTickets, deleteTicket, closeProject } from '../services/api';
import { ArrowLeft, Upload, XCircle, Lock, CheckCircle, Trash2 } from 'lucide-react';

const ProjectView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [closingProject, setClosingProject] = useState(false);

  useEffect(() => {
    loadProject();
    loadTickets();
  }, [id]);

  const loadProject = async () => {
    try {
      const response = await getProject(id);
      setProject(response.data);
    } catch (error) {
      console.error('Error loading project:', error);
      alert('Error al cargar proyecto');
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

  const handleDeleteTicket = async (ticketId) => {
    if (!window.confirm('¿Eliminar este ticket?')) return;
    
    try {
      await deleteTicket(ticketId);
      alert('✓ Ticket eliminado');
      loadTickets();
      loadProject(); // Actualizar totales
    } catch (error) {
      alert('Error al eliminar ticket');
    }
  };

  const handleCloseProject = async () => {
    if (!window.confirm('¿Cerrar proyecto? Se generará Excel y enviará email.')) return;
    
    setClosingProject(true);
    try {
      await closeProject(id);
      alert('✓ Proyecto cerrado. Excel generado y email enviado.');
      navigate('/dashboard');
    } catch (error) {
      alert('Error al cerrar proyecto');
      setClosingProject(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver al Dashboard</span>
          </button>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bebas tracking-wider">{project.creative_code}</h1>
                <span className={`px-3 py-1 text-xs font-mono tracking-wider rounded-sm border ${
                  project.status === 'en_curso'
                    ? 'bg-green-500/20 text-green-400 border-green-500/30'
                    : 'bg-gray-100 text-gray-800 border-gray-300'
                }`}>
                  {project.status === 'en_curso' ? 'EN CURSO' : 'CERRADO'}
                </span>
              </div>
              <p className="text-lg text-zinc-300 mb-1">{project.description}</p>
              <div className="flex items-center gap-4 text-sm text-zinc-500">
                <span>👤 {project.responsible}</span>
                <span>📅 {project.year}</span>
                <span>🏢 {project.company}</span>
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Actions */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => navigate(`/projects/${id}/upload`)}
            disabled={project.status === 'cerrado'}
            className="flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Upload size={18} />
            SUBIR TICKETS
          </button>
          
          {project.status === 'en_curso' && (
            <button
              onClick={handleCloseProject}
              disabled={closingProject || tickets.length === 0}
              className="flex items-center gap-2 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Lock size={18} />
              {closingProject ? 'CERRANDO...' : 'CERRAR PROYECTO'}
            </button>
          )}
        </div>

        {/* Tickets List */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bebas tracking-wider">TICKETS Y FACTURAS</h2>
            <span className="text-sm text-zinc-500">{tickets.length} tickets</span>
          </div>

          {tickets.length === 0 ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-12 text-center">
              <Upload size={48} className="mx-auto mb-4 text-zinc-600" />
              <p className="text-zinc-400 mb-2">No hay tickets en este proyecto</p>
              <p className="text-sm text-zinc-600">Haz click en "SUBIR TICKETS" para comenzar</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/tickets/${ticket.id}/review`)}
                  className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-4 cursor-pointer transition-all hover:shadow-lg hover:shadow-amber-500/10"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* EMOJI ESTADO REVISADO */}
                      <div className="flex items-center gap-2 mb-2">
                        {ticket.is_reviewed ? (
                          <span className="text-lg" title="Revisado">✅</span>
                        ) : (
                          <span className="text-lg" title="Pendiente revisión">👁️</span>
                        )}
                        <span className={`px-2 py-1 text-xs font-mono rounded-sm border ${
                          ticket.type === 'factura'
                            ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                            : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
                        }`}>
                          {ticket.type === 'factura' ? 'FACTURA' : 'TICKET'}
                        </span>
                      </div>

                      <h3 className="font-semibold mb-1">{ticket.provider}</h3>
                      <p className="text-sm text-zinc-400">
                        {ticket.date} • Nº {ticket.invoice_number || 'N/A'}
                      </p>
                    </div>
                    
                    <div className="text-right flex items-start gap-3">
                      <div>
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
            
            <div>
              <p className="text-zinc-500 mb-1">Email Cliente</p>
              <p className="text-zinc-100">{project.client_email || 'N/A'}</p>
            </div>
            
            <div>
              <p className="text-zinc-500 mb-1">Link Proyecto</p>
              {project.project_link ? (
                <a 
                  href={project.project_link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-amber-500 hover:text-amber-400 underline"
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
    </div>
  );
};

export default ProjectView;
