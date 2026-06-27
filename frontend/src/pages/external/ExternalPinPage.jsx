import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { validatePin } from '../../services/shareApi';
import { useExternalSession } from '../../context/ExternalSessionContext';

// Logo asterisco DAZZ (igual que Login)
const DazzLogo = () => (
  <div className="w-12 h-12 flex items-center justify-center text-amber-500">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-full h-full" strokeWidth="2.5" strokeLinecap="round">
      <line x1="12" y1="3" x2="12" y2="21" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="5.5" y1="5.5" x2="18.5" y2="18.5" />
      <line x1="18.5" y1="5.5" x2="5.5" y2="18.5" />
    </svg>
  </div>
);

const ExternalPinPage = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { loginGuest } = useExternalSession();

  const [pin, setPin] = useState('');
  const [inlineError, setInlineError] = useState('');   // PIN incorrecto (debajo del input)
  const [blockingError, setBlockingError] = useState(''); // expirado/revocado/bloqueado/inválido (card)
  const [loading, setLoading] = useState(false);

  const handlePinChange = (e) => {
    // Solo dígitos, máximo 6
    const digits = e.target.value.replace(/\D/g, '').slice(0, 6);
    setPin(digits);
    if (inlineError) setInlineError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (pin.length !== 6) {
      setInlineError('El PIN debe tener 6 dígitos');
      return;
    }
    setInlineError('');
    setBlockingError('');
    setLoading(true);
    try {
      const res = await validatePin(token, pin);
      const { access_token, guest_name, project_id } = res.data;
      // Guarda sesión + el share token (para que ExternalRoute/shareApi vuelvan al PIN tras 401)
      loginGuest(access_token, guest_name, project_id, token);
      // El token permanece en la ruta (/share/:token/...) por diseño; usamos replace
      // para no dejar la entrada del PIN en el historial.
      navigate(`/share/${token}/project`, { replace: true });
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || 'No se pudo validar el PIN';
      if (status === 401 && detail === 'PIN incorrecto') {
        setInlineError('PIN incorrecto');
        setPin('');
      } else {
        // "Este enlace ha caducado/revocado", "Demasiados intentos...", "Enlace no válido"
        setBlockingError(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo + marca */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <DazzLogo />
          </div>
          <h1 className="text-5xl font-bold mb-2 font-bebas tracking-wider">DAZZ CREATIVE</h1>
          <p className="text-zinc-500 text-sm tracking-widest font-mono">ACCESO AL PROYECTO</p>
        </div>

        {blockingError ? (
          /* Card de error bloqueante (no se puede seguir desde aquí) */
          <div className="bg-zinc-900 border border-red-500/30 rounded-sm p-8 text-center">
            <AlertCircle size={40} className="mx-auto text-red-400 mb-4" />
            <p className="text-red-400 font-semibold mb-2">{blockingError}</p>
            <p className="text-zinc-500 text-sm">
              Contacta con tu responsable en DAZZ para obtener un enlace nuevo.
            </p>
          </div>
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
            <h2 className="text-xl font-bebas tracking-wider mb-6 text-center">INTRODUCE TU PIN</h2>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  autoComplete="off"
                  autoFocus
                  value={pin}
                  onChange={handlePinChange}
                  placeholder="••••••"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-sm px-4 py-3 text-center text-2xl tracking-[0.5em] font-mono text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                />
                {inlineError && (
                  <p className="text-red-400 text-sm mt-2 text-center">{inlineError}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 hover:shadow-amber-500/50 tracking-wider disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-zinc-950 border-t-transparent" />
                    ENTRANDO...
                  </>
                ) : 'ENTRAR'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExternalPinPage;
