// AÑADIR ESTO EN ProjectView.jsx

// En la sección donde se muestran los tickets (línea ~150-200)
// Buscar donde renderizas cada ticket en la lista

{tickets.map((ticket) => (
  <div 
    key={ticket.id}
    onClick={() => navigate(`/tickets/${ticket.id}/review`)}
    className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-4 cursor-pointer transition-all hover:shadow-amber-500/10"
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        {/* ESTADO REVISADO - EMOJI */}
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

        {/* Resto del código del ticket... */}
        <h3 className="font-semibold mb-1">{ticket.provider}</h3>
        <p className="text-sm text-zinc-400">
          {ticket.date} • Nº {ticket.invoice_number || 'N/A'}
        </p>
      </div>
      
      <div className="text-right">
        <p className="text-xl font-bold text-amber-500">
          {ticket.final_total?.toFixed(2)}€
        </p>
        <p className="text-xs text-zinc-500">
          Base: {ticket.base_amount?.toFixed(2)}€
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
