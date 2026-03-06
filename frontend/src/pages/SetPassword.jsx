import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { setPassword as setPasswordAPI } from '../services/api';

const SetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (!tokenFromUrl) {
      setError('Token no encontrado. El enlace puede ser inválido.');
    } else {
      setToken(tokenFromUrl);
    }
  }, [searchParams]);

  const validatePassword = () => {
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return false;
    }
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validatePassword()) return;
    if (!token) {
      setError('Token inválido');
      return;
    }

    setLoading(true);

    try {
      const response = await setPasswordAPI(token, password);
      setSuccess(true);
      
      // Redirigir al login después de 2 segundos
      setTimeout(() => {
        navigate('/login');
      }, 2000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al configurar la contraseña. El token puede haber expirado.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8 text-center">
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bebas tracking-wider mb-3">¡CONTRASEÑA CONFIGURADA!</h2>
            <p className="text-zinc-400 mb-6">
              Tu contraseña ha sido actualizada correctamente.
            </p>
            <p className="text-sm text-zinc-500 mb-6">
              Redirigiendo al login...
            </p>
            <Link
              to="/login"
              className="inline-block px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all"
            >
              IR AL LOGIN
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 flex items-center justify-center text-amber-500">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-full h-full" strokeWidth="2.5" strokeLinecap="round">
                <line x1="12" y1="3" x2="12" y2="21" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="5.5" y1="5.5" x2="18.5" y2="18.5" />
                <line x1="18.5" y1="5.5" x2="5.5" y2="18.5" />
              </svg>
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-2 font-bebas tracking-wider">
            DAZZ CREATIVE
          </h1>
          <p className="text-zinc-500 text-sm tracking-widest font-mono">CONFIGURAR CONTRASEÑA</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
          <h2 className="text-xl font-semibold mb-2">Elige tu contraseña</h2>
          <p className="text-sm text-zinc-400 mb-6">
            Crea una contraseña segura para acceder al sistema.
          </p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
                NUEVA CONTRASEÑA
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="Mínimo 6 caracteres"
                autoComplete="new-password"
                required
                minLength={6}
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
                CONFIRMAR CONTRASEÑA
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="Repite la contraseña"
                autoComplete="new-password"
                required
                minLength={6}
              />
            </div>

            {error && (
              <div className="bg-red-900/20 border border-red-900/30 text-red-400 px-4 py-3 rounded-sm text-sm">
                {error}
              </div>
            )}

            {!token && (
              <div className="bg-yellow-900/20 border border-yellow-900/30 text-yellow-400 px-4 py-3 rounded-sm text-sm">
                ⚠️ Token no encontrado. Verifica que el enlace sea correcto.
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !token}
              className="w-full px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 hover:shadow-amber-500/50 tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'CONFIGURANDO...' : 'CONFIGURAR CONTRASEÑA'}
            </button>

            <div className="text-center pt-2">
              <Link 
                to="/login" 
                className="text-sm text-zinc-400 hover:text-amber-500 transition-colors"
              >
                ¿Ya tienes contraseña? Inicia sesión
              </Link>
            </div>
          </form>

          {/* Info panel */}
          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-sm">
            <p className="text-xs text-blue-400">
              <strong>💡 Consejo:</strong> Usa una contraseña segura que incluya letras, números y símbolos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetPassword;
