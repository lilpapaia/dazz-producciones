import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, CheckCircle } from 'lucide-react';
import { inviteSupplier } from '../../services/suppliersApi';

const SupplierInvite = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    setError('');
    setSending(true);

    try {
      await inviteSupplier({ name: name.trim(), email: email.trim() });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <div className="max-w-md mx-auto mt-12">
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-6 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-2">Invitation sent</h2>
          <p className="text-xs text-zinc-400 mb-4">
            An email has been sent to <span className="text-amber-400">{email}</span> with a registration link valid for 72 hours.
          </p>
          <div className="flex gap-2 justify-center">
            <button onClick={() => { setSent(false); setName(''); setEmail(''); }} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
              Invite another
            </button>
            <button onClick={() => navigate('/suppliers/list')} className="text-xs bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold px-4 py-2 rounded transition-colors">
              Go to suppliers
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-4">Invite supplier</h1>

      <div className="bg-zinc-900 border border-zinc-800 rounded-md p-5">
        <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-3 text-xs mb-5 leading-relaxed">
          The supplier will receive an email with a unique registration link valid for <strong>72 hours</strong>. They will set their own password during registration.
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">
              Name / Company name <span className="text-amber-500">*</span>
            </label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Estudio Martinez SL"
              required
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2.5 rounded focus:border-amber-500 outline-none"
            />
          </div>

          <div className="mb-4">
            <label className="text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">
              Email <span className="text-amber-500">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="supplier@example.com"
              required
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2.5 rounded focus:border-amber-500 outline-none"
            />
          </div>

          {error && (
            <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-xs mb-3">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={sending || !name.trim() || !email.trim()}
            className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-xs py-2.5 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Send size={14} />
            {sending ? 'Sending...' : 'Send invitation'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SupplierInvite;
