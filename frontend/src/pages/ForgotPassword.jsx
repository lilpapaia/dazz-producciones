import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { forgotPassword } from '../services/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await forgotPassword(email);
      setSuccess(true);
    } catch (err) {
      // Siempre mostramos éxito por seguridad (no revelar si email existe)
      setSuccess(true);
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
            <h2 className="text-2xl font-bebas tracking-wider mb-3">EMAIL ENVIADO</h2>
            <p className="text-zinc-400 mb-6">
              Si existe una cuenta con <span className="text-amber-500 font-mono">{email}</span>, recibirás un email con instrucciones para restablecer tu contraseña.
            </p>
            <p className="text-sm text-zinc-500 mb-6">
              Si no recibes el email en unos minutos, revisa tu carpeta de spam.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-amber-500 hover:text-amber-400 transition-colors"
            >
              <ArrowLeft size={16} />
              Volver al login
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
          <p className="text-zinc-500 text-sm tracking-widest font-mono">RECUPERAR CONTRASEÑA</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
          <Link
            to="/login"
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-6 text-sm"
          >
            <ArrowLeft size={16} />
            Volver al login
          </Link>

          <h2 className="text-xl font-semibold mb-2">¿Olvidaste tu contraseña?</h2>
          <p className="text-sm text-zinc-400 mb-6">
            Introduce tu email y te enviaremos un enlace para crear una nueva contraseña.
          </p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100 focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="tu@email.com"
                autoComplete="email"
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
              {loading ? 'ENVIANDO...' : 'ENVIAR EMAIL'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
