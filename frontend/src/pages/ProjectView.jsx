import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjectTickets, closeProject, deleteTicket } from '../services/api';
import { ArrowLeft, Upload, FileText, Trash2, CheckCircle } from 'lucide-react';

const ProjectView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [projectRes, ticketsRes] = await Promise.all([
        getProject(id),
        getProjectTickets(id)
      ]);
      setProject(projectRes.data);
      setTickets(ticketsRes.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al cargar proyecto');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async () => {
    if (!confirm('¿Cerrar proyecto? Se generará Excel y se enviará email.')) return;
    
    try {
      await closeProject(id);
      alert('✓ Proyecto cerrado exitosamente\n✓ Excel generado\n✓ Email enviado');
      navigate('/dashboard');
    } catch (error) {
      alert('Error al cerrar proyecto');
    }
  };

  const handleDeleteTicket = async (ticketId, e) => {
    e.stopPropagation();
    if (!confirm('¿Eliminar este ticket?')) return;
    
    try {
      await deleteTicket(ticketId);
      loadData();
    } catch (error) {
      alert('Error al eliminar ticket');
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
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver al Dashboard</span>
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bebas tracking-wider">{project.description}</h1>
              <p className="text-sm text-zinc-500 font-mono mt-1">{project.creative_code}</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate(`/projects/${id}/upload`)}
                className="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold flex items-center gap-2"
              >
                <Upload size={18} /> SUBIR TICKETS
              </button>
              {project.status === 'en_curso' && (
                <button
                  onClick={handleClose}
                  className="px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 flex items-center gap-2"
                >
                  <CheckCircle size={18} /> CERRAR PROYECTO
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 mb-6">
          <h2 className="text-xl font-bebas tracking-wider mb-4">INFORMACIÓN DEL PROYECTO</h2>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-zinc-500 font-mono mb-1">RESPONSABLE</p>
              <p className="font-semibold">{project.responsible}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 font-mono mb-1">TOTAL TICKETS</p>
              <p className="font-semibold">{tickets.length}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 font-mono mb-1">IMPORTE TOTAL</p>
              <p className="text-2xl font-bold text-amber-500">
                {tickets.reduce((sum, t) => sum + (t.final_total || 0), 0).toFixed(2)}€
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 font-mono mb-1">ESTADO</p>
              <span className={`inline-block px-3 py-1 text-xs font-mono tracking-wider rounded-sm border ${
                project.status === 'en_curso'
                  ? 'bg-green-500/20 text-green-400 border-green-500/30'
                  : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
              }`}>
                {project.status === 'en_curso' ? 'EN CURSO' : 'CERRADO'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bebas tracking-wider">TICKETS Y FACTURAS</h2>
            {tickets.length === 0 && (
              <button
                onClick={() => navigate(`/projects/${id}/upload`)}
                className="text-sm text-amber-500 hover:text-amber-400 font-medium"
              >
                Subir primer ticket
              </button>
            )}
          </div>

          {tickets.length === 0 ? (
            <div className="text-center py-12">
              <FileText size={48} className="mx-auto text-zinc-700 mb-4" />
              <p className="text-zinc-500 mb-2">No hay tickets subidos aún</p>
              <p className="text-sm text-zinc-600">Sube facturas o tickets de gastos</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/tickets/${ticket.id}/review`)}
                  className="bg-zinc-950 border border-zinc-700 hover:border-amber-500/50 rounded-sm p-4 cursor-pointer transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold">{ticket.provider}</h3>
                        <span className={`px-2 py-0.5 text-xs font-mono rounded-sm ${
                          ticket.type === 'factura'
                            ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            : 'bg-zinc-700/50 text-zinc-400 border border-zinc-600'
                        }`}>
                          {ticket.type === 'factura' ? 'FACTURA' : 'TICKET'}
                        </span>
                        {ticket.invoice_number && (
                          <span className="text-xs text-zinc-500 font-mono">Nº {ticket.invoice_number}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-6 text-sm">
                        <span className="text-zinc-500 font-mono">{ticket.date}</span>
                        {ticket.invoice_status && (
                          <span className={`px-2 py-0.5 text-xs font-mono rounded-sm ${
                            ticket.invoice_status === 'RECIBIDO' 
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-amber-500/20 text-amber-400'
                          }`}>
                            {ticket.invoice_status}
                          </span>
                        )}
                        {ticket.payment_status && (
                          <span className={`px-2 py-0.5 text-xs font-mono rounded-sm ${
                            ticket.payment_status?.includes('PAGADO')
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {ticket.payment_status}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <div>
                        <p className="text-2xl font-bold text-amber-500">{ticket.final_total?.toFixed(2)}€</p>
                        <p className="text-xs text-zinc-500 font-mono mt-1">Base: {ticket.base_amount?.toFixed(2)}€</p>
                      </div>
                      {project.status === 'en_curso' && (
                        <button
                          onClick={(e) => handleDeleteTicket(ticket.id, e)}
                          className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-sm transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ProjectView;
