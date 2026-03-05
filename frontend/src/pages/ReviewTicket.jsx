import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTicket, updateTicket } from '../services/api';
import { ArrowLeft, Save, X, ZoomIn, ChevronLeft, ChevronRight } from 'lucide-react';

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
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showLightbox, setShowLightbox] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => { 
    loadTicket(); 
    setCurrentPage(0);
  }, [id]);

  const loadTicket = async () => {
    try {
      const response = await getTicket(id);
      console.log('Ticket recibido:', response.data);
      console.log('file_pages tipo:', typeof response.data.file_pages);
      console.log('file_pages valor:', response.data.file_pages);
      setTicket(response.data);
    } catch (error) {
      alert('Error al cargar ticket');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTicket(id, {...ticket, is_reviewed: true});
      alert('✓ Ticket actualizado y marcado como revisado');
      navigate(-1);
    } catch (error) {
      alert('Error al actualizar ticket');
    } finally {
      setSaving(false);
    }
  };

  // Obtener array de páginas - VERSION SIMPLIFICADA Y ROBUSTA
  const getPages = () => {
    if (!ticket) return [];
    
    // Si file_pages existe, procesarlo
    if (ticket.file_pages) {
      // Caso 1: Ya es un array (axios lo parseó)
      if (Array.isArray(ticket.file_pages)) {
        console.log('file_pages es array:', ticket.file_pages.length, 'páginas');
        return ticket.file_pages;
      }
      
      // Caso 2: Es un string JSON, parsearlo
      if (typeof ticket.file_pages === 'string') {
        try {
          const parsed = JSON.parse(ticket.file_pages);
          if (Array.isArray(parsed)) {
            console.log('file_pages parseado:', parsed.length, 'páginas');
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

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  const pages = getPages();
  const totalPages = pages.length;
  
  console.log('Páginas finales:', pages);
  console.log('Total páginas:', totalPages);
  console.log('Página actual:', currentPage);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3">
            <ArrowLeft size={18} />
            <span className="text-sm">Volver</span>
          </button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-bebas tracking-wider">REVISAR TICKET</h1>
            {ticket.is_reviewed ? <span className="text-2xl">✅</span> : <span className="text-2xl">👁️</span>}
            {ticket.is_foreign && (
              <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded text-xs font-bold uppercase border border-blue-500/30">
                🌍 Internacional
              </span>
            )}
          </div>
          <span className={`inline-block mt-2 px-3 py-1 text-xs font-mono tracking-wider rounded-sm border ${
            ticket.type === 'factura' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
          }`}>
            {ticket.type === 'factura' ? 'FACTURA' : 'TICKET'}
          </span>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-6 pb-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 space-y-6">

          {/* VISOR GALERÍA */}
          {pages.length > 0 && (
            <div className="bg-zinc-950 border border-zinc-700 rounded-sm overflow-hidden">
              
              {/* Imagen principal */}
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

              {/* Controles navegación */}
              <div className="px-4 py-3 bg-zinc-900/80 border-t border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {/* Flechas */}
                  <button
                    onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                    disabled={currentPage === 0 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft size={18} />
                  </button>

                  <span className="text-sm font-mono text-zinc-300">
                    {totalPages > 1 ? `${currentPage + 1} / ${totalPages}` : ticket.file_name}
                  </span>

                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={currentPage === totalPages - 1 || totalPages <= 1}
                    className="p-1.5 rounded-sm bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>

                {/* Dots indicadores */}
                {totalPages > 1 && (
                  <div className="flex gap-1.5">
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
            </div>
          )}

          {/* LIGHTBOX */}
          {showLightbox && pages.length > 0 && (
            <div
              className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
              onClick={() => setShowLightbox(false)}
            >
              <button
                onClick={(e) => { e.stopPropagation(); setShowLightbox(false); }}
                className="absolute top-4 right-4 text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700"
              >
                <X size={32} />
              </button>

              {/* Flecha izquierda lightbox */}
              {totalPages > 1 && currentPage > 0 && (
                <button
                  onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p - 1); }}
                  className="absolute left-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700"
                >
                  <ChevronLeft size={28} />
                </button>
              )}

              <img
                src={pages[currentPage]}
                alt={`Página ${currentPage + 1}`}
                className="max-w-full max-h-[90vh] object-contain shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              />

              {/* Flecha derecha lightbox */}
              {totalPages > 1 && currentPage < totalPages - 1 && (
                <button
                  onClick={(e) => { e.stopPropagation(); setCurrentPage(p => p + 1); }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 bg-zinc-900/80 hover:bg-zinc-700 text-white p-3 rounded-full border border-zinc-700"
                >
                  <ChevronRight size={28} />
                </button>
              )}

              {/* Contador lightbox */}
              {totalPages > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-900/80 px-4 py-2 rounded-full text-sm font-mono text-zinc-300 border border-zinc-700">
                  {currentPage + 1} / {totalPages}
                </div>
              )}
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
                    <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-sm">{ticket.currency}</span>
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
                  <p className="text-xs text-zinc-500 mb-2">Importes en divisa original:</p>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-zinc-400 text-xs">Base original</p>
                      <p className="font-semibold text-blue-400">{ticket.foreign_amount.toFixed(2)} {ticket.currency}</p>
                    </div>
                    {ticket.foreign_tax_amount && (
                      <div>
                        <p className="text-zinc-400 text-xs">IVA original</p>
                        <p className="font-semibold text-blue-400">{ticket.foreign_tax_amount.toFixed(2)} {ticket.currency}</p>
                      </div>
                    )}
                    {ticket.foreign_tax_eur && (
                      <div>
                        <p className="text-zinc-400 text-xs">IVA reclamable</p>
                        <p className="font-bold text-green-400">{ticket.foreign_tax_eur.toFixed(2)}€ ✅</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Fecha y Proveedor */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">FECHA FACTURA</label>
              <input type="text" value={ticket.date || ''} onChange={(e) => setTicket({...ticket, date: e.target.value})}
                placeholder="DD/MM/AAAA" className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">PROVEEDOR *</label>
              <input type="text" value={ticket.provider || ''} onChange={(e) => setTicket({...ticket, provider: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
            </div>
          </div>

          {ticket.type === 'factura' && (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">Nº FACTURA</label>
                <input type="text" value={ticket.invoice_number || ''} onChange={(e) => setTicket({...ticket, invoice_number: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">TELÉFONO</label>
                <input type="text" value={ticket.phone || ''} onChange={(e) => setTicket({...ticket, phone: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
                <input type="email" value={ticket.email || ''} onChange={(e) => setTicket({...ticket, email: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
              </div>
            </div>
          )}

          {ticket.type === 'factura' && (
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOMBRE CONTACTO</label>
              <input type="text" value={ticket.contact_name || ''} onChange={(e) => setTicket({...ticket, contact_name: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500" />
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

          {/* Notas */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOTAS (PO SI APLICA)</label>
            <textarea value={ticket.notes || ''} onChange={(e) => setTicket({...ticket, notes: e.target.value})}
              rows={3} placeholder="Descripción del gasto, observaciones..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 resize-none" />
          </div>

          {/* Estados */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS FACTURA</label>
              <select value={ticket.invoice_status || ''} onChange={(e) => setTicket({...ticket, invoice_status: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500">
                <option value="">Seleccionar...</option>
                {invoiceStatusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ESTATUS PAGO</label>
              <select value={ticket.payment_status || ''} onChange={(e) => setTicket({...ticket, payment_status: e.target.value})}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500">
                <option value="">Seleccionar...</option>
                {paymentStatusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <button onClick={() => navigate(-1)} className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold">
              Cancelar
            </button>
            <button onClick={handleSave} disabled={saving}
              className="flex-1 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2">
              <Save size={18} />
              {saving ? 'GUARDANDO...' : 'MARCAR REVISADO ✓'}
            </button>
          </div>

        </div>
      </main>
    </div>
  );
};

export default ReviewTicket;
