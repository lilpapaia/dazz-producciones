import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, CheckCircle, Shield } from 'lucide-react';
import { inviteSupplier, createOC } from '../../services/suppliersApi';
import { getCompanies } from '../../services/api';

const SupplierInvite = () => {
  const navigate = useNavigate();
  const [type, setType] = useState('talent'); // 'talent' | 'general'
  const [companies, setCompanies] = useState([]);

  // Talent fields (step 1: create OC)
  const [talentName, setTalentName] = useState('');
  const [talentNif, setTalentNif] = useState('');
  const [talentOC, setTalentOC] = useState('');
  const [mgmtCompanyId, setMgmtCompanyId] = useState(null);
  const [ocCreated, setOcCreated] = useState(false);

  // Shared fields (step 2 talent / step 1 general)
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const [sending, setSending] = useState(false);
  const [creatingOC, setCreatingOC] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getCompanies().then(r => {
      setCompanies(r.data);
      const mgmt = r.data.find(c => c.name.toUpperCase().includes('MGMT'));
      if (mgmt) setMgmtCompanyId(mgmt.id);
    }).catch(() => {});
  }, []);

  const handleCreateOC = async () => {
    if (!talentName.trim() || !talentOC.trim()) return;
    setError('');
    setCreatingOC(true);
    try {
      await createOC({
        oc_number: talentOC.trim(),
        talent_name: talentName.trim(),
        nif_cif: talentNif.trim() || null,
        company_id: mgmtCompanyId,
      });
      setOcCreated(true);
      setName(talentName);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create OC');
    } finally {
      setCreatingOC(false);
    }
  };

  const handleInvite = async (e) => {
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

  const reset = () => {
    setType('talent');
    setTalentName(''); setTalentNif(''); setTalentOC('');
    setOcCreated(false);
    setName(''); setEmail('');
    setSent(false); setError('');
  };

  // ─── SUCCESS STATE ───
  if (sent) {
    return (
      <div className="max-w-lg mx-auto mt-12">
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-6 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-2">Invitation sent</h2>
          <p className="text-xs text-zinc-400 mb-4">
            An email has been sent to <span className="text-amber-400">{email}</span> with a registration link valid for 72 hours.
          </p>
          <div className="flex gap-2 justify-center">
            <button onClick={reset} className="text-xs px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
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

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-xs px-3 py-2.5 rounded focus:border-amber-500 outline-none";
  const labelCls = "text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-4">Invite supplier</h1>

      {/* Info bar */}
      <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-3 text-xs mb-4 leading-relaxed">
        The supplier receives a unique secure link (72h) to register — they fill in their details, upload bank certificate and create their own password.
      </div>

      {/* Type selector */}
      <div className="mb-4">
        <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-2">Supplier type *</div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { key: 'talent', label: 'Talent / Influencer', desc: 'Permanent OC · DAZZLE MGMT only' },
            { key: 'mixed', label: 'Mixed', desc: 'Permanent OC + project OCs · All companies' },
            { key: 'general', label: 'General supplier', desc: 'Project OC per invoice · All companies' },
          ].map(opt => (
            <button
              key={opt.key}
              type="button"
              onClick={() => { setType(opt.key); setOcCreated(false); setError(''); }}
              className={`border rounded-md p-3 text-left transition-all ${
                type === opt.key
                  ? 'border-amber-500 bg-amber-500/[.04]'
                  : 'border-zinc-700 bg-zinc-900 hover:border-zinc-500'
              }`}
            >
              <div className={`w-3 h-3 border-2 rounded-full mb-2 relative ${type === opt.key ? 'border-amber-500' : 'border-zinc-600'}`}>
                {type === opt.key && <div className="absolute inset-[3px] bg-amber-500 rounded-full" />}
              </div>
              <div className={`font-['Bebas_Neue'] text-xs tracking-wide ${type === opt.key ? 'text-amber-400' : 'text-zinc-300'}`}>{opt.label}</div>
              <div className="text-[9px] text-zinc-500 mt-0.5">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ─── TALENT / MIXED FLOW (both need OC creation) ─── */}
      {(type === 'talent' || type === 'mixed') && (
        <>
          {/* Step 1: Create OC */}
          <div className={`bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3 transition-opacity ${ocCreated ? 'opacity-40 pointer-events-none' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm flex-shrink-0 ${ocCreated ? 'bg-zinc-700 text-green-400' : 'bg-amber-500 text-zinc-950'}`}>
                {ocCreated ? '✓' : '1'}
              </div>
              <div>
                <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Create permanent OC</div>
                <div className="text-[10px] text-zinc-500">Invoices to DAZZLE MGMT only &middot; OC auto-assigned on registration via NIF</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2.5 mb-3">
              <div>
                <label className={labelCls}>Talent name <span className="text-amber-500">*</span></label>
                <input value={talentName} onChange={e => setTalentName(e.target.value)} placeholder="@mariagomez" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>NIF / DNI</label>
                <input value={talentNif} onChange={e => setTalentNif(e.target.value)} placeholder="12345678A" className={inputCls} />
                <div className="text-[9px] text-zinc-600 mt-0.5">For auto-matching on registration</div>
              </div>
              <div>
                <label className={labelCls}>Company</label>
                <input value="DAZZLE MGMT" disabled className="w-full bg-zinc-700 border border-zinc-700 text-zinc-500 text-xs px-3 py-2.5 rounded cursor-not-allowed" />
              </div>
            </div>

            <div className="grid grid-cols-[1fr_2fr] gap-2.5 mb-3">
              <div>
                <label className={labelCls}>OC code <span className="text-amber-500">*</span></label>
                <input value={talentOC} onChange={e => setTalentOC(e.target.value)} placeholder="OC-MGMTINT2026047" className={`${inputCls} font-mono`} />
                <div className="text-[9px] text-zinc-600 mt-0.5">Sequential accounting number</div>
              </div>
              {talentNif && talentOC && (
                <div className="flex items-end pb-0.5">
                  <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] flex items-start gap-2 flex-1">
                    <Shield size={13} className="flex-shrink-0 mt-0.5" />
                    On registration with NIF {talentNif}, the system auto-assigns {talentOC}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleCreateOC}
                disabled={creatingOC || !talentName.trim() || !talentOC.trim()}
                className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-xs px-4 py-2 rounded transition-colors disabled:opacity-50"
              >
                {creatingOC ? 'Creating...' : 'Create OC →'}
              </button>
            </div>
          </div>

          {/* Step 2: Send invitation */}
          <div className={`bg-zinc-900 border border-zinc-800 rounded-md p-4 transition-opacity ${!ocCreated ? 'opacity-40 pointer-events-none' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-7 h-7 bg-amber-500 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm text-zinc-950 flex-shrink-0">2</div>
              <div>
                <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Send invitation email</div>
                <div className="text-[10px] text-zinc-500">The supplier creates their own password during registration</div>
              </div>
            </div>

            <form onSubmit={handleInvite}>
              <div className="grid grid-cols-2 gap-2.5 mb-3">
                <div>
                  <label className={labelCls}>Email <span className="text-amber-500">*</span></label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="talent@email.com" required className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>Name</label>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder={talentName || 'Supplier name'} className={inputCls} />
                </div>
              </div>

              <div className="mb-3">
                <label className={labelCls}>Custom message</label>
                <input placeholder="Hello, here's your access to the supplier portal..." className={inputCls} />
              </div>

              <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] mb-3 flex items-start gap-2">
                <Shield size={13} className="flex-shrink-0 mt-0.5" />
                The supplier will need: NIF/CIF, IBAN and bank certificate PDF. Link valid 72h.
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={sending || !email.trim() || !name.trim()}
                  className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-xs px-4 py-2 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <Send size={13} />
                  {sending ? 'Sending...' : 'Send invitation'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {/* ─── GENERAL FLOW ─── */}
      {type === 'general' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-7 h-7 bg-amber-500 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm text-zinc-950 flex-shrink-0">1</div>
            <div>
              <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Send invitation email</div>
              <div className="text-[10px] text-zinc-500">General suppliers don't have a fixed OC — they use the project OC on each invoice</div>
            </div>
          </div>

          <form onSubmit={handleInvite}>
            <div className="grid grid-cols-2 gap-2.5 mb-3">
              <div>
                <label className={labelCls}>Name / Company name <span className="text-amber-500">*</span></label>
                <input value={name} onChange={e => setName(e.target.value)} placeholder="Audiovisual Pérez SL" required className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Email <span className="text-amber-500">*</span></label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="contacto@empresa.com" required className={inputCls} />
              </div>
            </div>

            <div className="mb-3">
              <label className={labelCls}>Custom message</label>
              <textarea placeholder="Hello, we invite you to register as a supplier for DAZZ Creative..." className={`${inputCls} resize-none`} rows={2} />
            </div>

            <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] mb-3 flex items-start gap-2">
              <Shield size={13} className="flex-shrink-0 mt-0.5" />
              The supplier will need: NIF/CIF, IBAN and bank certificate PDF. Creates their own password. Link valid 72h.
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={sending || !name.trim() || !email.trim()}
                className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-xs px-4 py-2 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <Send size={13} />
                {sending ? 'Sending...' : 'Send invitation'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-xs mt-3">
          {error}
        </div>
      )}
    </div>
  );
};

export default SupplierInvite;
