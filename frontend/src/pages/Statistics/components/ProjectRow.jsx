import { memo } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import TicketRow from './TicketRow';

const ProjectRow = memo(({ project, isMobile, indent = false, isExpanded, onToggle, onNavigate }) => {
  const claimableTickets = (project.tickets || []).filter(t => t.foreign_tax_eur > 0);

  return (
    <div className={`space-y-2 ${indent ? 'ml-6' : ''}`}>
      <div
        onClick={() => onToggle(project.id)}
        className={`bg-zinc-900 border border-zinc-800 rounded-sm p-4 transition-colors cursor-pointer ${
          isMobile ? 'active:bg-zinc-800' : 'hover:border-amber-500'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {isExpanded
              ? <ChevronDown size={18} className="text-amber-500 flex-shrink-0" />
              : <ChevronRight size={18} className="text-zinc-600 flex-shrink-0" />
            }
            <div className="min-w-0">
              <p className="font-semibold text-sm text-zinc-100 mb-1 truncate">
                {project.description?.startsWith(project.creative_code)
                  ? project.description.slice(project.creative_code.length).trim() || project.description
                  : project.description}
              </p>
              <div className="flex flex-col gap-1 text-xs text-zinc-500">
                <span className="font-mono truncate">{project.creative_code}</span>
                <span className="bg-zinc-800 px-2 py-0.5 rounded self-start">
                  {claimableTickets.length} ticket{claimableTickets.length !== 1 ? 's' : ''} con IVA reclamable
                </span>
              </div>
            </div>
          </div>
          <div className="text-right flex-shrink-0 ml-3">
            <p className="font-bold text-amber-500">
              {project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
            </p>
            {project.foreign_amount && (
              <p className="text-xs text-zinc-500">
                ({project.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {project.currency})
              </p>
            )}
          </div>
        </div>
      </div>

      {isExpanded && claimableTickets.length > 0 && (
        <div className="ml-8 space-y-2">
          <p className="text-xs text-zinc-600 font-semibold uppercase mb-2">Tickets internacionales:</p>
          {claimableTickets.map(ticket => (
            <TicketRow key={ticket.id} ticket={ticket} projectId={project.id} isMobile={isMobile} onNavigate={onNavigate} />
          ))}
        </div>
      )}
    </div>
  );
});

ProjectRow.displayName = 'ProjectRow';

export default ProjectRow;
