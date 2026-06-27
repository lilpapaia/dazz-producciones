import { useState, useEffect, useCallback } from 'react';
import { Link2, Trash2, X, RefreshCw, Copy, ChevronDown } from 'lucide-react';
import { getShareTokens, revokeShareToken, hideShareToken, regenerateSharePin } from '../services/api';
import { showSuccess, showError } from '../utils/toast';
import ConfirmDialog from './ConfirmDialog';

// Tiempo relativo simple en español para "último acceso".
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return 'Sin acceder';
  const then = new Date(dateStr).getTime();
  if (isNaN(then)) return 'Sin acceder';
  const diff = Date.now() - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Hace un momento';
  if (mins < 60) return `Hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Hace ${hours} h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `Hace ${days} día${days !== 1 ? 's' : ''}`;
  return new Date(dateStr).toLocaleDateString('es-ES');
};

const statusBadge = (token) => {
  if (!token.is_active) return <span className="bg-zinc-700/50 text-zinc-400 border border-zinc-600/30 px-2 py-0.5 rounded-sm text-xs font-bold">REVOCADO</span>;
  if (token.is_expired) return <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-sm text-xs font-bold">EXPIRADO</span>;
  return <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-sm text-xs font-bold">ACTIVO</span>;
};

const copyToClipboard = async (text, label) => {
  try {
    await navigator.clipboard.writeText(text);
    showSuccess(`${label} copiado`);
  } catch {
    showError('No se pudo copiar al portapapeles');
  }
};

// FEAT-09: panel de enlaces externos de un proyecto (solo producción, no MGMT).
const ShareLinksPanel = ({ projectId, companyName, refreshSignal }) => {
  const [tokens, setTokens] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState(null);
  const [expandedId, setExpandedId] = useState(null);      // link activo expandido (ver URL / regenerar PIN)
  const [regenerating, setRegenerating] = useState(null);  // id en curso de regeneración
  const [newPins, setNewPins] = useState({});              // id → PIN recién regenerado

  const isMgmt = (companyName || '').toUpperCase().includes('MGMT');

  const load = useCallback(async () => {
    try {
      const res = await getShareTokens(projectId);
      setTokens(res.data);
    } catch {
      // silencioso: el panel simplemente no se muestra si falla
    } finally {
      setLoaded(true);
    }
  }, [projectId]);

  useEffect(() => {
    if (!isMgmt) load();
  }, [load, isMgmt, refreshSignal]);

  const confirmRevoke = async () => {
    const target = revokeTarget;
    setRevokeTarget(null);
    if (!target) return;
    try {
      await revokeShareToken(projectId, target.id);
      showSuccess('Enlace revocado');
      load();
    } catch (e) {
      showError(e.response?.data?.detail || 'Error al revocar el enlace');
    }
  };

  // Ocultar un link revocado del panel (no se borra de BD).
  const handleHide = async (token) => {
    setTokens(prev => prev.filter(t => t.id !== token.id)); // optimista
    try {
      await hideShareToken(projectId, token.id);
    } catch (e) {
      showError(e.response?.data?.detail || 'Error al ocultar el enlace');
      load(); // revertir si falla
    }
  };

  const handleRegenerate = async (token) => {
    setRegenerating(token.id);
    try {
      const res = await regenerateSharePin(projectId, token.id);
      setNewPins(prev => ({ ...prev, [token.id]: res.data.pin }));
      showSuccess('PIN regenerado');
    } catch (e) {
      showError(e.response?.data?.detail || 'Error al regenerar el PIN');
    } finally {
      setRegenerating(null);
    }
  };

  const toggleExpand = (token) => {
    setExpandedId(prev => (prev === token.id ? null : token.id));
  };

  // No mostrar en MGMT, ni hasta cargar, ni si no hay tokens.
  if (isMgmt || !loaded || tokens.length === 0) return null;

  const visible = showAll ? tokens : tokens.slice(0, 3);

  return (
    <div className="mt-8 bg-zinc-900 border border-zinc-800 rounded-sm p-6">
      <h3 className="text-sm font-bebas tracking-wider flex items-center gap-2 mb-4 text-zinc-300">
        <Link2 size={16} className="text-blue-400" />
        ENLACES EXTERNOS ({tokens.length})
      </h3>

      <div className="space-y-2">
        {visible.map((token) => {
          const clickable = token.is_active && !token.is_expired;
          const expanded = expandedId === token.id;
          const newPin = newPins[token.id];
          return (
            <div key={token.id} className="bg-zinc-950 border border-zinc-800 rounded-sm overflow-hidden">
              <div className="flex items-center justify-between gap-3 p-3">
                <button
                  type="button"
                  onClick={() => clickable && toggleExpand(token)}
                  disabled={!clickable}
                  className={`min-w-0 text-left flex-1 ${clickable ? 'cursor-pointer' : 'cursor-default'}`}
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-zinc-100 text-sm truncate">{token.guest_name}</span>
                    {statusBadge(token)}
                    {clickable && (
                      <ChevronDown
                        size={14}
                        className={`text-zinc-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
                      />
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1 flex-wrap">
                    <span>Expira: {new Date(token.expires_at).toLocaleDateString('es-ES')}</span>
                    <span>•</span>
                    <span>{formatRelativeTime(token.last_accessed_at)}</span>
                    {token.created_by_name && (<><span>•</span><span>por {token.created_by_name}</span></>)}
                  </div>
                </button>

                {token.is_active ? (
                  <button
                    onClick={() => setRevokeTarget(token)}
                    className="flex-shrink-0 p-2 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-sm transition-colors"
                    title="Revocar acceso"
                  >
                    <Trash2 size={16} />
                  </button>
                ) : (
                  <button
                    onClick={() => handleHide(token)}
                    className="flex-shrink-0 p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-700/40 rounded-sm transition-colors"
                    title="Ocultar de la lista"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>

              {clickable && expanded && (
                <div className="px-3 pb-3 pt-1 border-t border-zinc-800/70 space-y-3">
                  {/* URL del enlace */}
                  <div>
                    <label className="block text-xs text-zinc-500 mb-1">Enlace de acceso</label>
                    <div className="flex items-center gap-2">
                      <input
                        readOnly
                        value={token.share_url}
                        onFocus={(e) => e.target.select()}
                        className="flex-1 min-w-0 bg-zinc-900 border border-zinc-700 text-zinc-300 px-3 py-2 rounded-sm text-xs font-mono truncate"
                      />
                      <button
                        onClick={() => copyToClipboard(token.share_url, 'Enlace')}
                        className="flex-shrink-0 p-2 text-zinc-400 hover:text-amber-400 hover:bg-amber-500/10 rounded-sm transition-colors"
                        title="Copiar enlace"
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Regenerar PIN */}
                  {newPin ? (
                    <div>
                      <label className="block text-xs text-zinc-500 mb-1">Nuevo PIN</label>
                      <div className="flex items-center gap-2">
                        <span className="flex-1 font-mono text-xl tracking-widest text-amber-400 bg-zinc-900 border border-amber-500/30 px-3 py-2 rounded-sm text-center">
                          {newPin}
                        </span>
                        <button
                          onClick={() => copyToClipboard(newPin, 'PIN')}
                          className="flex-shrink-0 p-2 text-zinc-400 hover:text-amber-400 hover:bg-amber-500/10 rounded-sm transition-colors"
                          title="Copiar PIN"
                        >
                          <Copy size={16} />
                        </button>
                      </div>
                      <p className="text-xs text-amber-500/80 mt-1">El PIN anterior ya no es válido.</p>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleRegenerate(token)}
                      disabled={regenerating === token.id}
                      className="flex items-center gap-2 text-sm text-amber-500 hover:text-amber-400 font-semibold transition-colors disabled:opacity-50"
                    >
                      <RefreshCw size={15} className={regenerating === token.id ? 'animate-spin' : ''} />
                      {regenerating === token.id ? 'Regenerando…' : 'Regenerar PIN'}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {tokens.length > 3 && (
        <button
          onClick={() => setShowAll(s => !s)}
          className="mt-3 text-xs text-amber-500 hover:text-amber-400 font-semibold transition-colors"
        >
          {showAll ? 'Ver menos' : `Ver todos (${tokens.length})`}
        </button>
      )}

      <ConfirmDialog
        isOpen={!!revokeTarget}
        onClose={() => setRevokeTarget(null)}
        onConfirm={confirmRevoke}
        title="¿Revocar acceso?"
        message={`El enlace de "${revokeTarget?.guest_name}" dejará de funcionar de inmediato. Esta acción no se puede deshacer.`}
        confirmText="Revocar"
        cancelText="Cancelar"
        type="danger"
      />
    </div>
  );
};

export default ShareLinksPanel;
