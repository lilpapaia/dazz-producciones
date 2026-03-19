import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { validateToken, registerSupplier, uploadBankCert } from '../services/api';
import { CheckCircle, AlertCircle, FileText } from 'lucide-react';

const Register = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { login } = useAuth();
  const token = params.get('token') || '';

  const [step, setStep] = useState(1); // 1: details, 2: banking, 3: password
  const [tokenValid, setTokenValid] = useState(null);
  const [invitation, setInvitation] = useState({});
  const [form, setForm] = useState({ name: '', nif_cif: '', phone: '', address: '', iban: '', password: '', confirmPassword: '', gdpr_consent: false });
  const [bankCertFile, setBankCertFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [certFailed, setCertFailed] = useState(false);
  const [certRetrying, setCertRetrying] = useState(false);

  useEffect(() => {
    if (!token) { setTokenValid(false); return; }
    validateToken(token).then(({ data }) => {
      setTokenValid(data.valid);
      if (data.valid) { setInvitation(data); setForm(f => ({ ...f, name: data.name || '' })); }
    }).catch(() => setTokenValid(false));
  }, [token]);

  const set = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const handleSubmit = async () => {
    setError('');
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return; }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return; }
    if (!/[A-Z]/.test(form.password)) { setError('Password must contain at least one uppercase letter'); return; }
    if (!/[0-9]/.test(form.password)) { setError('Password must contain at least one number'); return; }
    if (!/[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\;'/`~]/.test(form.password)) { setError('Password must contain at least one special character'); return; }
    if (!form.gdpr_consent) { setError('You must accept the data processing terms'); return; }

    setLoading(true);
    try {
      const { data } = await registerSupplier({
        token,
        name: form.name,
        nif_cif: form.nif_cif || null,
        phone: form.phone || null,
        address: form.address || null,
        iban: form.iban || null,
        password: form.password,
        gdpr_consent: true,
      });
      login({ access_token: data.access_token, refresh_token: data.refresh_token, supplier: { id: data.supplier_id, name: form.name, email: invitation.email } });

      // Upload bank cert if provided
      if (bankCertFile) {
        try {
          await uploadBankCert(bankCertFile);
        } catch {
          setCertFailed(true);
          setLoading(false);
          return; // Don't navigate — show retry banner
        }
      }

      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === null) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (tokenValid === false) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="text-center max-w-sm">
        <AlertCircle size={40} className="text-red-400 mx-auto mb-3" />
        <h2 className="font-['Bebas_Neue'] text-xl text-zinc-100 mb-2">Invalid or expired link</h2>
        <p className="text-xs text-zinc-500">This registration link is invalid, expired, or has already been used. Please contact the DAZZ admin team.</p>
      </div>
    </div>
  );

  const handleRetryCert = async () => {
    setCertRetrying(true);
    try {
      await uploadBankCert(bankCertFile);
      setCertFailed(false);
      navigate('/');
    } catch {
      setCertRetrying(false);
    }
  };

  if (certFailed) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-2">Account created</h2>
          <div className="bg-amber-500/[.08] text-amber-400 border border-amber-500/[.15] rounded-md p-3 text-xs mb-4 text-left leading-relaxed">
            <strong>Bank certificate upload failed.</strong> Your account is active but the certificate was not uploaded. You can retry now or upload it later from your profile.
          </div>
          <div className="flex gap-2">
            <button onClick={handleRetryCert} disabled={certRetrying}
              className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-2.5 rounded-md transition-colors disabled:opacity-50">
              {certRetrying ? 'Uploading...' : 'Retry upload'}
            </button>
            <button onClick={() => navigate('/')}
              className="flex-1 text-sm py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
              Continue anyway
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-sm px-3 py-2.5 rounded-md focus:border-amber-500 outline-none";
  const labelCls = "text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1.5 block";

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="font-['Bebas_Neue'] text-2xl tracking-wider text-amber-500">DAZZ SUPPLIERS</h1>
          <p className="text-xs text-zinc-500 mt-1">Create your account</p>
        </div>

        {/* Progress */}
        <div className="flex gap-1 mb-1.5">
          {[1, 2, 3].map(s => (
            <div key={s} className={`flex-1 h-1 rounded-full ${s <= step ? 'bg-amber-500' : 'bg-zinc-800'}`} />
          ))}
        </div>
        <div className="flex justify-between text-[9px] text-zinc-600 mb-5">
          <span>Details</span><span>Banking</span><span>Password</span>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
          {/* Step 1: Details */}
          {step === 1 && (
            <>
              <div className="mb-3">
                <label htmlFor="reg-name" className={labelCls}>Name / Company <span className="text-amber-500">*</span></label>
                <input id="reg-name" value={form.name} onChange={set('name')} required className={inputCls} />
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label htmlFor="reg-nif" className={labelCls}>NIF/CIF/VAT</label>
                  <input id="reg-nif" value={form.nif_cif} onChange={set('nif_cif')} placeholder="e.g. 12345678A" className={inputCls} />
                </div>
                <div>
                  <label htmlFor="reg-phone" className={labelCls}>Phone</label>
                  <input id="reg-phone" value={form.phone} onChange={set('phone')} placeholder="+34 600..." className={inputCls} />
                </div>
              </div>
              <div className="mb-4">
                <label htmlFor="reg-address" className={labelCls}>Fiscal address</label>
                <input id="reg-address" value={form.address} onChange={set('address')} placeholder="Street, city, country" className={inputCls} />
              </div>
              <button onClick={() => setStep(2)} disabled={!form.name.trim()} className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-2.5 rounded-md transition-colors disabled:opacity-50">
                Continue
              </button>
            </>
          )}

          {/* Step 2: Banking */}
          {step === 2 && (
            <>
              <div className="mb-3">
                <label htmlFor="reg-iban" className={labelCls}>IBAN <span className="text-amber-500">*</span></label>
                <input id="reg-iban" value={form.iban} onChange={set('iban')} placeholder="ES12 1234 5678 9012 3456 7890" className={inputCls} />
                <p className="text-[10px] text-zinc-600 mt-1">Your IBAN will be encrypted and stored securely.</p>
              </div>
              <div className="mb-4">
                <label className={labelCls}>Bank certificate (PDF) <span className="text-amber-500">*</span></label>
                {bankCertFile ? (
                  <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-md p-2.5">
                    <FileText size={16} className="text-red-400 flex-shrink-0" />
                    <span className="text-xs text-zinc-300 truncate flex-1">{bankCertFile.name}</span>
                    <button type="button" onClick={() => setBankCertFile(null)} className="text-[10px] text-zinc-500 hover:text-zinc-300">Remove</button>
                  </div>
                ) : (
                  <label className="block border-2 border-dashed border-zinc-700 rounded-md p-4 text-center cursor-pointer hover:border-amber-500 transition-colors">
                    <FileText size={20} className="text-zinc-600 mx-auto mb-1" />
                    <span className="text-xs text-zinc-400">Tap to select PDF</span>
                    <input type="file" accept=".pdf,application/pdf" onChange={e => { if (e.target.files?.[0]) setBankCertFile(e.target.files[0]); }} className="hidden" />
                  </label>
                )}
                <p className="text-[10px] text-zinc-600 mt-1">Document proving bank account ownership (required by DAZZ).</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setStep(1)} className="flex-1 text-sm py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Back</button>
                <button onClick={() => setStep(3)} disabled={!form.iban.trim() || !bankCertFile} className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-2.5 rounded-md transition-colors disabled:opacity-50">Continue</button>
              </div>
            </>
          )}

          {/* Step 3: Password + RGPD */}
          {step === 3 && (
            <>
              <div className="mb-3">
                <label htmlFor="reg-password" className={labelCls}>Password <span className="text-amber-500">*</span></label>
                <input id="reg-password" type="password" value={form.password} onChange={set('password')} placeholder="Min 8 chars, 1 uppercase, 1 number, 1 special" className={inputCls} />
              </div>
              <div className="mb-4">
                <label htmlFor="reg-confirm" className={labelCls}>Confirm password <span className="text-amber-500">*</span></label>
                <input id="reg-confirm" type="password" value={form.confirmPassword} onChange={set('confirmPassword')} className={inputCls} />
              </div>

              <label className="flex items-start gap-2 mb-4 cursor-pointer">
                <input type="checkbox" checked={form.gdpr_consent} onChange={set('gdpr_consent')} className="mt-0.5 accent-amber-500" />
                <span className="text-[11px] text-zinc-400 leading-relaxed">
                  I consent to the processing of my personal data in accordance with GDPR and the <a href="#" className="text-amber-500 underline">privacy policy</a>.
                </span>
              </label>

              {error && (
                <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-3">{error}</div>
              )}

              <div className="flex gap-2">
                <button onClick={() => setStep(2)} className="flex-1 text-sm py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Back</button>
                <button onClick={handleSubmit} disabled={loading} className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-2.5 rounded-md transition-colors disabled:opacity-50">
                  {loading ? 'Creating...' : 'Create account'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Register;
