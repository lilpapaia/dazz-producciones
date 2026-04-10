import { memo } from 'react';
import { FileText } from 'lucide-react';

const TicketRow = memo(({ ticket, projectId, isMobile, onNavigate }) => (
  <div
    onClick={(e) => {
      e.stopPropagation();
      onNavigate(`/tickets/${ticket.id}/review?filter=international&project=${projectId}`);
    }}
    className={`bg-zinc-900/50 border border-zinc-800 rounded-sm p-3 transition-colors cursor-pointer group ${
      isMobile ? 'active:border-blue-500' : 'hover:border-blue-500'
    }`}
  >
    <div className={`flex ${isMobile ? 'flex-col gap-2' : 'items-center justify-between'}`}>
      <div className="flex items-center gap-3 min-w-0">
        <FileText size={16} className="text-zinc-600 group-hover:text-blue-400 transition-colors flex-shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100 truncate">{ticket.provider}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-zinc-600">{ticket.date}</span>
            {ticket.invoice_number && (
              <>
                <span className="text-zinc-700">&bull;</span>
                <span className="text-xs text-zinc-600 font-mono truncate">{ticket.invoice_number}</span>
              </>
            )}
          </div>
        </div>
      </div>
      <div className={`flex-shrink-0 ${isMobile ? 'flex items-center gap-3 ml-7 flex-wrap' : 'text-right'}`}>
        <p className="text-sm font-bold text-zinc-300">
          {ticket.final_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
        </p>
        {ticket.foreign_amount && (
          <p className="text-xs text-zinc-600">
            {ticket.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {ticket.currency}
          </p>
        )}
        {ticket.foreign_tax_eur && (
          <p className="text-xs text-green-500 font-semibold">
            IVA: {ticket.foreign_tax_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
          </p>
        )}
      </div>
    </div>
  </div>
));

TicketRow.displayName = 'TicketRow';

export default TicketRow;
