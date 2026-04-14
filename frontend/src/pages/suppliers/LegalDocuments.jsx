import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Users, ChevronRight, AlertCircle, Loader2 } from 'lucide-react';
import { getLegalDocumentStats } from '../../services/suppliersApi';

const TYPE_CONFIG = {
  PRIVACY: { badge: 'TODOS', badgeCls: 'bg-blue-400/20 text-blue-400', label: 'Todos los proveedores' },
  CONTRACT: { badge: 'INFLUENCERS', badgeCls: 'bg-purple-400/20 text-purple-400', label: 'Solo influencers' },
  AUTOCONTROL: { badge: 'INFLUENCERS', badgeCls: 'bg-purple-400/20 text-purple-400', label: 'Solo influencers' },
  DECLARATION: { badge: 'INFLUENCERS', badgeCls: 'bg-purple-400/20 text-purple-400', label: 'Solo influencers' },
};

const LegalDocumentsPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getLegalDocumentStats()
      .then(r => setStats(r.data))
      .catch(() => setError('Error al cargar documentos'));
  }, []);

  if (!stats && !error) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Stats endpoint already filters to generic-only docs
  const genericDocs = stats || [];

  return (
    <div className="max-w-[47rem] mx-auto">
      <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-4">Documentos legales</h1>

      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-3 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      <div className="space-y-3">
        {genericDocs.map(doc => {
          const config = TYPE_CONFIG[doc.type] || TYPE_CONFIG.PRIVACY;
          const pct = doc.total_applicable > 0 ? Math.round((doc.total_accepted / doc.total_applicable) * 100) : 0;
          const isPlaceholder = doc.total_applicable > 0 && doc.total_accepted === 0 && doc.version === 1;

          return (
            <div key={doc.id} className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
              {/* Header */}
              <div className="flex items-start gap-3 mb-3">
                <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <FileText size={16} className="text-amber-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[13px] font-medium text-zinc-200">{doc.title}</span>
                    <span className="text-[10px] text-zinc-500 font-['IBM_Plex_Mono']">v{doc.version}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${config.badgeCls}`}>{config.badge}</span>
                    <span className="text-[10px] text-zinc-600">
                      Actualizado {new Date(doc.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-zinc-400">
                    {doc.total_accepted}/{doc.total_applicable} aceptados
                  </span>
                  <span className="text-[11px] text-zinc-500">{pct}%</span>
                </div>
                <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${pct === 100 ? 'bg-green-400' : pct > 0 ? 'bg-amber-500' : 'bg-zinc-700'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                {doc.total_applicable - doc.total_accepted > 0 && (
                  <button
                    onClick={() => navigate(`/suppliers/documents/${doc.id}/pending`)}
                    className="text-[12px] text-zinc-400 hover:text-zinc-200 border border-zinc-700 px-3 py-1.5 rounded transition-colors flex items-center gap-1.5"
                  >
                    <Users size={12} />
                    Ver pendientes ({doc.total_applicable - doc.total_accepted})
                  </button>
                )}
                <button
                  onClick={() => navigate(`/suppliers/documents/update/${doc.type}`)}
                  className="text-[12px] text-amber-400 hover:text-amber-300 border border-amber-500/30 px-3 py-1.5 rounded transition-colors ml-auto"
                >
                  {doc.type === 'CONTRACT' ? 'Actualizar contratos' : 'Actualizar'} <ChevronRight size={12} className="inline" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {genericDocs.length === 0 && !error && (
        <div className="text-center py-12 text-zinc-500 text-sm">
          No hay documentos legales configurados.
        </div>
      )}
    </div>
  );
};

export default LegalDocumentsPage;
