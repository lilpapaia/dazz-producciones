import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginSupplier } from '../services/api';
import DazzLogo from '../components/DazzLogo';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await loginSupplier({ email, password });
      login(data);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <DazzLogo size={40} className="w-10 h-10 text-amber-500 mx-auto mb-3" />
          <h1 className="font-['Bebas_Neue'] text-2xl tracking-wider text-zinc-100">DAZZ SUPPLIERS</h1>
          <p className="text-xs text-zinc-500 mt-1">Supplier Portal</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="mb-4">
            <label htmlFor="sup-email" className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1.5 block">Email</label>
            <input
              id="sup-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-md focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none"
            />
          </div>

          <div className="mb-5">
            <label htmlFor="sup-password" className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1.5 block">Password</label>
            <input
              id="sup-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-md focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none"
            />
          </div>

          {error && (
            <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-4">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-3 rounded-md transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-[11px] text-zinc-600 mt-4">
          Need an account? Contact the DAZZ admin team.
        </p>
      </div>
    </div>
  );
};

export default Login;
