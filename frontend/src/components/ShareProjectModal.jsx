import { useState } from 'react';
import { X, Copy, Check, Link2, KeyRound } from 'lucide-react';
import { createShareToken } from '../services/api';
import { showError } from '../utils/toast';

// FEAT-09: modal para generar un enlace + PIN de acceso externo a un proyecto.
const ShareProjectModal = ({ projectId, isOpen, onClose, onGenerated }) => {
  const [guestName, setGuestName] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null); // { shareUrl, pin, guestName }
  const [copied, setCopied] = useState(''); // 'link' | 'pin'

  // Fecha mínima = mañana
  const tomorrow = (() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  })();

  const reset = () => {
    setGuestName('');
    setExpiresAt('');
    setResult(null);
    setCopied('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleGenerate = async () => {
    if (!guestName.trim() || !expiresAt) return;
    setGenerating(true);
    try {
      // expires_at a fin del día elegido (23:59:59) para que el día completo sea válido
      const expiresIso = new Date(`${expiresAt}T23:59:59`).toISOString();
      const res = await createShareToken(projectId, {
        guest_name: guestName.trim(),
        expires_at: expiresIso,
      });
      const shareUrl = `${window.location.origin}/share/${res.data.token}`;
      setResult({ shareUrl, pin: res.data.pin, guestName: res.data.guest_name });
      if (onGenerated) onGenerated();
    } catch (e) {
      showError(e.response?.data?.detail || 'Error al generar el enlace');
    } finally {
      setGenerating(false);
    }
  };

  const copy = async (text, which) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(which);
      setTimeout(() => setCopied(''), 2000);
    } catch {
      showError('No se pudo copiar al portapapeles');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4" onClick={handleClose}>
      <div className="bg-zinc-900 border border-zinc-800 rounded-sm max-w-md w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-zinc-800">
          <h3 className="text-xl font-bebas tracking-wider flex items-center gap-2">
            <Link2 size={20} className="text-blue-400" />
            COMPARTIR PROYECTO
          </h3>
          <button onClick={handleClose} className="text-zinc-400 hover:text-zinc-100 transition-colors p-1">
            <X size={20} />
          </button>
        </div>

        {!result ? (
          /* ── Formulario ── */
          <div className="p-6 space-y-4">
            <p className="text-sm text-zinc-400">
              Genera un enlace con PIN para que una persona externa suba y gestione tickets en este proyecto, sin necesidad de cuenta.
            </p>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-1.5 tracking-wider">NOMBRE DEL EXTERNO</label>
              <input
                type="text"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
                placeholder="Ej: Carlos Producer"
                className="w-full bg-zinc-950 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-sm focus:border-amber-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-1.5 tracking-wider">FECHA DE EXPIRACIÓN</label>
              <input
                type="date"
                value={expiresAt}
                min={tomorrow}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-sm focus:border-amber-500 outline-none [color-scheme:dark]"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={!guestName.trim() || !expiresAt || generating}
              className="w-full bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold py-3 rounded-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {generating ? 'GENERANDO...' : 'GENERAR ENLACE'}
            </button>
          </div>
        ) : (
          /* ── Resultado ── */
          <div className="p-6 space-y-5">
            <p className="text-sm text-zinc-300">
              Enlace generado para <span className="font-semibold text-amber-400">{result.guestName}</span>.
            </p>

            {/* Link */}
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-1.5 tracking-wider flex items-center gap-1.5">
                <Link2 size={13} /> ENLACE
              </label>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={result.shareUrl}
                  onFocus={(e) => e.target.select()}
                  className="flex-1 min-w-0 bg-zinc-950 border border-zinc-700 text-zinc-300 text-xs px-3 py-2.5 rounded-sm font-mono"
                />
                <button
                  onClick={() => copy(result.shareUrl, 'link')}
                  className="flex-shrink-0 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-sm transition-colors"
                  title="Copiar enlace"
                >
                  {copied === 'link' ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            {/* PIN */}
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-1.5 tracking-wider flex items-center gap-1.5">
                <KeyRound size={13} /> PIN
              </label>
              <div className="flex gap-2">
                <div className="flex-1 bg-zinc-950 border border-zinc-700 rounded-sm py-2.5 text-center">
                  <span className="font-mono text-2xl tracking-[0.4em] text-amber-400">{result.pin}</span>
                </div>
                <button
                  onClick={() => copy(result.pin, 'pin')}
                  className="flex-shrink-0 px-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-sm transition-colors"
                  title="Copiar PIN"
                >
                  {copied === 'pin' ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 rounded-sm p-3">
              <p className="text-xs text-blue-300">
                🔒 Por seguridad, envía el <strong>enlace por email</strong> y el <strong>PIN por WhatsApp</strong> (canales separados). El PIN no se vuelve a mostrar.
              </p>
            </div>

            <button
              onClick={handleClose}
              className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold py-3 rounded-sm transition-colors"
            >
              Cerrar
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShareProjectModal;
