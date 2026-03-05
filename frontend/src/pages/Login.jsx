import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as loginApi } from '../services/api';

const Login = () => {
  const [identifier, setIdentifier] = useState(''); // ← Cambiado de 'email' a 'identifier'
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginApi(identifier, password); // ← Envía identifier
      login(response.data.access_token, response.data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

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
          <p className="text-zinc-500 text-sm tracking-widest font-mono">SISTEMA GESTIÓN GASTOS</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
          <h2 className="text-xl font-semibold mb-6">Iniciar Sesión</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              {/* ← Cambiado label y tipo de input */}
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
                EMAIL O USUARIO
              </label>
              <input
                type="text" // ← Cambiado de "email" a "text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="usuario o email"
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">CONTRASEÑA</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            {error && (
              <div className="bg-red-900/20 border border-red-900/30 text-red-400 px-4 py-3 rounded-sm text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 hover:shadow-amber-500/50 tracking-wider disabled:opacity-50"
            >
              {loading ? 'ENTRANDO...' : 'ENTRAR'}
            </button>

            {/* ← Link a forgot password */}
            <div className="text-center pt-2">
              <Link 
                to="/forgot-password" 
                className="text-sm text-zinc-400 hover:text-amber-500 transition-colors"
              >
                ¿Olvidaste tu contraseña?
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
