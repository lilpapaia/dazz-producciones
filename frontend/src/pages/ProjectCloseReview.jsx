import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjectTickets, closeProjectWithEmails, getUsernames } from '../services/api';
import { ArrowLeft, Download, Send, FileSpreadsheet, AlertCircle } from 'lucide-react';
import EmailChipsInput from '../components/EmailChipsInput';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatusBadge from '../components/common/StatusBadge';

const ProjectCloseReview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [emailRecipients, setEmailRecipients] = useState([]);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [projectRes, ticketsRes, usersRes] = await Promise.all([
        getProject(id),
        getProjectTickets(id),
        getUsernames()
      ]);
      
      setProject(projectRes.data);
      setTickets(ticketsRes.data);
      setUsers(usersRes.data);
      
      // Buscar email del responsable en la lista de usuarios
      const responsibleUser = usersRes.data.find(
        u => u.name.toLowerCase() === projectRes.data.responsible.toLowerCase()
      );
      
      if (responsibleUser) {
        setEmailRecipients([responsibleUser.email]);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al cargar datos');
      navigate(`/projects/${id}`);
    } finally {
      setLoading(false);
    }
  };

  // Obtener email del responsable para mostrar info
  const getResponsibleEmail = () => {
    if (!project || users.length === 0) return null;
    const user = users.find(u => u.name.toLowerCase() === project.responsible.toLowerCase());
    return user?.email || null;
  };

  const handleConfirmClose = async () => {
    // Validar que haya al menos un email
    if (emailRecipients.length === 0) {
      alert('⚠️ Debes añadir al menos un destinatario de email');
      return;
    }

    if (!window.confirm(`¿Confirmar cierre? Se enviará email a ${emailRecipients.length} destinatario(s) y se descargará Excel.`)) return;

    setSending(true);
    try {
      // Llamada backend con emails personalizados
      const response = await closeProjectWithEmails(id, emailRecipients);
      
      // Descargar Excel automáticamente
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${project.creative_code}_GASTOS.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert(`✓ Proyecto cerrado. Excel descargado y email enviado a ${emailRecipients.length} destinatario(s).`);
      navigate('/dashboard');
    } catch (error) {
      console.error('Error closing project:', error);
      alert('Error al cerrar proyecto: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  const totalAmount = tickets.reduce((sum, t) => sum + (t.final_total || 0), 0);
  const responsibleEmail = getResponsibleEmail();

  if (loading) return <LoadingSpinner size="lg" fullPage />;

  if (!project) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <p className="text-zinc-400">No se pudo cargar el proyecto</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate(`/projects/${id}`)}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver al Proyecto</span>
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bebas tracking-wider">CERRAR PROYECTO</h1>
              <p className="text-zinc-400">{project.creative_code} • {project.description}</p>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm text-zinc-500">TOTAL PROYECTO</p>
                <p className="text-3xl font-bold text-amber-500">{totalAmount.toFixed(2)}€</p>
              </div>
              <FileSpreadsheet size={48} className="text-green-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-8">
        {/* Alerta Importante */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-sm p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle size={24} className="text-amber-500 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-500 mb-1">Revisa los datos y destinatarios antes de confirmar</p>
              <p className="text-sm text-zinc-400">
                Al confirmar se enviará el Excel por email a los destinatarios seleccionados, 
                se descargará una copia local y el proyecto quedará marcado como CERRADO.
              </p>
            </div>
          </div>
        </div>

        {/* Preview Excel - Tabla de Tickets */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm overflow-hidden mb-6">
          <div className="px-6 py-4 bg-zinc-800 border-b border-zinc-700">
            <h2 className="text-lg font-bebas tracking-wider flex items-center gap-2">
              <FileSpreadsheet size={20} className="text-green-500" />
              PREVIEW EXCEL - {tickets.length} TICKETS
            </h2>
          </div>

          {/* Tabla */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800/50 text-zinc-400 text-xs font-mono">
                <tr>
                  <th className="px-4 py-3 text-left">TIPO</th>
                  <th className="px-4 py-3 text-left">FECHA</th>
                  <th className="px-4 py-3 text-left">PROVEEDOR</th>
                  <th className="px-4 py-3 text-left">Nº FACTURA</th>
                  <th className="px-4 py-3 text-right">BASE</th>
                  <th className="px-4 py-3 text-right">IVA</th>
                  <th className="px-4 py-3 text-right">TOTAL</th>
                  <th className="px-4 py-3 text-left">ESTADO FACTURA</th>
                  <th className="px-4 py-3 text-left">ESTADO PAGO</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket, index) => (
                  <tr 
                    key={ticket.id}
                    className={`border-t border-zinc-800 hover:bg-zinc-800/30 ${
                      index % 2 === 0 ? 'bg-zinc-900' : 'bg-zinc-900/50'
                    }`}
                  >
                    <td className="px-4 py-3">
                      <StatusBadge type="ticket" value={ticket.type} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{ticket.date || 'N/A'}</td>
                    <td className="px-4 py-3">{ticket.provider}</td>
                    <td className="px-4 py-3 font-mono text-xs">{ticket.invoice_number || '-'}</td>
                    <td className="px-4 py-3 text-right font-mono">{ticket.base_amount?.toFixed(2)}€</td>
                    <td className="px-4 py-3 text-right font-mono">{ticket.iva_amount?.toFixed(2)}€</td>
                    <td className="px-4 py-3 text-right font-bold text-amber-500">{ticket.final_total?.toFixed(2)}€</td>
                    <td className="px-4 py-3 text-xs text-zinc-400">{ticket.invoice_status || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-sm ${
                        ticket.payment_status?.includes('PAGADO')
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {ticket.payment_status || 'PENDIENTE'}
                      </span>
                    </td>
                  </tr>
                ))}

                {/* Fila Total */}
                <tr className="bg-zinc-800 border-t-2 border-amber-500 font-bold">
                  <td colSpan="6" className="px-4 py-3 text-right">TOTAL PROYECTO:</td>
                  <td className="px-4 py-3 text-right text-xl text-amber-500">{totalAmount.toFixed(2)}€</td>
                  <td colSpan="2"></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Información Email - CON SELECTOR DE DESTINATARIOS */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 mb-6">
          <h3 className="text-lg font-bebas tracking-wider mb-4">INFORMACIÓN ENVÍO</h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Columna Izquierda: Emails */}
            <div>
              <EmailChipsInput
                emails={emailRecipients}
                onChange={setEmailRecipients}
                label="Destinatarios Email"
              />
              
              {emailRecipients.length > 0 && (
                <div className="mt-3 p-3 bg-zinc-950 border border-zinc-700 rounded-sm">
                  <p className="text-xs text-zinc-500 mb-1">Se enviará a:</p>
                  <div className="space-y-1">
                    {emailRecipients.map((email, index) => (
                      <p key={index} className="text-sm text-zinc-300">
                        📧 {email}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Columna Derecha: Info Proyecto */}
            <div className="space-y-4">
              <div>
                <p className="text-zinc-500 text-sm mb-1">Responsable Proyecto</p>
                <p className="text-zinc-100 font-semibold">{project.responsible}</p>
                {responsibleEmail && (
                  <p className="text-xs text-zinc-500 mt-1">📧 {responsibleEmail}</p>
                )}
                {!responsibleEmail && (
                  <p className="text-xs text-amber-500 mt-1">⚠️ Usuario no encontrado en el sistema</p>
                )}
              </div>

              <div>
                <p className="text-zinc-500 text-sm mb-1">Nombre Archivo</p>
                <p className="text-zinc-100 font-mono text-sm">{project.creative_code}_GASTOS.xlsx</p>
              </div>
              
              <div>
                <p className="text-zinc-500 text-sm mb-1">Total Tickets</p>
                <p className="text-zinc-100">{tickets.length} tickets</p>
              </div>
              
              <div>
                <p className="text-zinc-500 text-sm mb-1">Importe Total</p>
                <p className="text-2xl font-bold text-amber-500">{totalAmount.toFixed(2)}€</p>
              </div>
            </div>
          </div>
        </div>

        {/* Botones de Acción */}
        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/projects/${id}`)}
            className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
          >
            Cancelar
          </button>
          
          <button
            onClick={handleConfirmClose}
            disabled={sending || tickets.length === 0 || emailRecipients.length === 0}
            className="flex-1 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {sending ? (
              <>
                <LoadingSpinner size="sm" color="dark" />
                PROCESANDO...
              </>
            ) : (
              <>
                <Send size={18} />
                <Download size={18} />
                CONFIRMAR Y ENVIAR
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
};

export default ProjectCloseReview;

