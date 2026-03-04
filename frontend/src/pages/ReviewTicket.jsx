import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTicket, updateTicket } from '../services/api';
import { ArrowLeft, Save, X, ZoomIn } from 'lucide-react';

const invoiceStatusOptions = [
  "RECIBIDO",
  "PEDIDO",
  "PENDIENTE PEDIR",
  "RECIBIDO PERO ERRONEO",
  "TICKET (NO FACTURA)",
  "A REPARTIR EN STATEMENT",
  "ALTA SS",
  "PERDIDO"
];

const paymentStatusOptions = [
  "PENDIENTE",
  "PAGADO REVOLUT",
  "ADELANTADO",
  "REPARTIR STATEMENT TALENT",
  "PAGADO TARJETA PERSONAL",
  "PAGADO CAJA",
  "PAGADO SABADELL",
  "PAGADO BBVA"
];

const ReviewTicket = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showLightbox, setShowLightbox] = useState(false);

  useEffect(() => {
    loadTicket();
  }, [id]);

  const loadTicket = async () => {
    try {
      const response = await getTicket(id);
      setTicket(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al cargar ticket');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTicket(id, ticket);
      alert('✓ Ticket actualizado correctamente');
      navigate(-1);
    } catch (error) {
      alert('Error al actualizar ticket');
    } finally {
      setSaving(false);
    }
  };

  const getImageUrl = () => {
    if (!ticket?.file_path) return null;
    // El backend sirve archivos desde /uploads
    return `http://localhost:8000/${ticket.file_path}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  const imageUrl = getImageUrl();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver</span>
          </button>
          <h1 className="text-3xl font-bebas tracking-wider">REVISAR TICKET</h1>
          <span className={`inline-block mt-2 px-3 py-1 text-xs font-mono tracking-wider rounded-sm border ${
            ticket.type === 'factura'
              ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
              : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
          }`}>
            {ticket.type === 'factura' ? 'FACTURA' : 'TICKET'}
          </span>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 space-y-6">
          
          {/* VISTA PREVIA DEL TICKET - MINIATURA CLICKEABLE CON LIGHTBOX */}
          {imageUrl && (
            <div className="bg-zinc-950 border border-zinc-700 rounded-sm overflow-hidden">
              <div 
                onClick={() => setShowLightbox(true)}
                className="relative cursor-pointer group"
              >
                <img 
                  src={imageUrl} 
                  alt="Vista previa del ticket"
                  className="w-full h-64 object-contain bg-zinc-900"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><text x="50%" y="50%" text-anchor="middle" fill="%23555" font-size="16">Error cargando imagen</text></svg>';
                  }}
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-all flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="bg-amber-500 text-zinc-950 p-3 rounded-full shadow-lg">
                      <ZoomIn size={24} />
                    </div>
                  </div>
                </div>
              </div>
              <div className="px-4 py-2 bg-zinc-900/50 border-t border-zinc-800">
                <p className="text-xs text-zinc-500 font-mono">
                  <ZoomIn size={14} className="inline mr-1" />
                  Click para ver en tamaño completo
                </p>
              </div>
            </div>
          )}

          {/* LIGHTBOX MODAL - IMAGEN COMPLETA */}
          {showLightbox && imageUrl && (
            <div 
              className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
              onClick={() => setShowLightbox(false)}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowLightbox(false);
                }}
                className="absolute top-4 right-4 text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700"
              >
                <X size={32} />
              </button>
              <div className="max-w-7xl max-h-full">
                <img 
                  src={imageUrl} 
                  alt="Ticket completo"
                  className="max-w-full max-h-[90vh] object-contain shadow-2xl"
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          )}

          {/* Alerta IA */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-sm p-4">
            <div className="flex items-start gap-3">
              <div className="text-blue-400 mt-0.5">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-400">Datos extraídos por IA</p>
                <p className="text-xs text-zinc-400 mt-1">Revisa la información y corrige si es necesario</p>
              </div>
            </div>
          </div>

          {/* Fecha y Proveedor */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">FECHA FACTURA</label>
              <input
                type="date"
                value={ticket.date || ''}
                onChange={(e) => setTicket({...ticket, date: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">PROVEEDOR *</label>
              <input
                type="text"
                value={ticket.provider || ''}
                onChange={(e) => setTicket({...ticket, provider: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>
          </div>

          {/* Campos adicionales para facturas */}
          {ticket.type === 'factura' && (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">Nº FACTURA</label>
                <input
                  type="text"
                  value={ticket.invoice_number || ''}
                  onChange={(e) => setTicket({...ticket, invoice_number: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">TELÉFONO</label>
                <input
                  type="text"
                  value={ticket.phone || ''}
                  onChange={(e) => setTicket({...ticket, phone: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
                <input
                  type="email"
                  value={ticket.email || ''}
                  onChange={(e) => setTicket({...ticket, email: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          )}

          {/* Nombre contacto (facturas) */}
          {ticket.type === 'factura' && (
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOMBRE CONTACTO</label>
              <input
                type="text"
                value={ticket.contact_name || ''}
                onChange={(e) => setTicket({...ticket, contact_name: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
              />
            </div>
          )}

          {/* Desglose importes */}
          <div className="bg-zinc-950 border border-zinc-700 rounded-sm p-4">
            <p className="text-xs text-zinc-500 font-mono mb-3 tracking-wider">DESGLOSE IMPORTES</p>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-zinc-400 mb-1 text-xs">Base</p>
                <p className="font-semibold">{ticket.base_amount?.toFixed(2)}€</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1 text-xs">% IVA</p>
                <p className="font-semibold">{(ticket.iva_percentage * 100).toFixed(0)}%</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1 text-xs">IVA</p>
                <p className="font-semibold">{ticket.iva_amount?.toFixed(2)}€</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1 text-xs">Total</p>
                <p className="text-xl font-bold text-amber-500">{ticket.final_total?.toFixed(2)}€</p>
              </div>
            </div>
          </div>

          {/* NOTAS (PO SI APLICA) */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOTAS (PO SI APLICA)</label>
            <textarea
              value={ticket.notes || ''}
              onChange={(e) => setTicket({...ticket, notes: e.target.value})}
              rows={3}
              placeholder="Descripción del gasto, observaciones..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors resize-none"
            />
          </div>

          {/* Estados: FACTURA y PAGO */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS FACTURA</label>
              <select
                value={ticket.invoice_status || ''}
                onChange={(e) => setTicket({...ticket, invoice_status: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
              >
                <option value="">Seleccionar...</option>
                {invoiceStatusOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS PAGO</label>
              <select
                value={ticket.payment_status || ''}
                onChange={(e) => setTicket({...ticket, payment_status: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
              >
                <option value="">Seleccionar...</option>
                {paymentStatusOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={() => navigate(-1)}
              className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Save size={18} />
              {saving ? 'GUARDANDO...' : 'MARCAR REVISADO'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ReviewTicket;
