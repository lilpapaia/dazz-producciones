import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTicket, updateTicket } from '../services/api';
import { ArrowLeft, Save } from 'lucide-react';

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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver</span>
          </button>
          <h1 className="text-3xl font-bebas tracking-wider">REVISAR TICKET</h1>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 space-y-6">
          {/* Tipo de documento */}
          <div>
            <span className={`px-3 py-1.5 text-sm font-mono tracking-wider rounded-sm border ${
              ticket.type === 'factura'
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
            }`}>
              {ticket.type === 'factura' ? 'FACTURA' : 'TICKET'}
            </span>
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
            <p className="text-xs text-zinc-500 font-mono mb-3">DESGLOSE IMPORTES</p>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-zinc-400 mb-1">Base</p>
                <p className="font-semibold">{ticket.base_amount?.toFixed(2)}€</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1">% IVA</p>
                <p className="font-semibold">{ticket.iva_percentage || '21'}%</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1">IVA</p>
                <p className="font-semibold">{ticket.iva_amount?.toFixed(2) || '0.00'}€</p>
              </div>
              <div>
                <p className="text-zinc-400 mb-1">Total</p>
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
