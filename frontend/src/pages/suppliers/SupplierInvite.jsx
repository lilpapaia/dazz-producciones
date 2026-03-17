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
  const [message, setMessage] = useState('');

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
      setError(err.response?.data?.detail || 'Error al crear OC');
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
      await inviteSupplier({ name: name.trim(), email: email.trim(), message: message.trim() || undefined, supplier_type: type });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al enviar invitación');
    } finally {
      setSending(false);
    }
  };

  const reset = () => {
    setType('talent');
    setTalentName(''); setTalentNif(''); setTalentOC('');
    setOcCreated(false);
    setName(''); setEmail(''); setMessage('');
    setSent(false); setError('');
  };

  // ─── SUCCESS STATE ───
  if (sent) {
    return (
      <div className="max-w-lg mx-auto mt-12">
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-6 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-2">Invitación enviada</h2>
          <p className="text-[13px] text-zinc-400 mb-4">
            Se ha enviado un email a <span className="text-amber-400">{email}</span> con un link de registro válido durante 72 horas.
          </p>
          <div className="flex gap-2 justify-center">
            <button onClick={reset} className="text-[13px] px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
              Invitar otro
            </button>
            <button onClick={() => navigate('/suppliers/list')} className="text-[13px] bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold px-4 py-2 rounded transition-colors">
              Ir a proveedores
            </button>
          </div>
        </div>
      </div>
    );
  }

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2.5 rounded focus:border-amber-500 outline-none";
  const labelCls = "text-[11px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-4">Invitar proveedor</h1>

      {/* Info bar */}
      <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-3 text-[13px] mb-4 leading-relaxed">
        El proveedor recibe un link único seguro (72h) para registrarse — rellena todos sus datos, sube el certificado bancario y crea su propia contraseña.
      </div>

      {/* Type selector */}
      <div className="mb-4">
        <div className="text-[12px] text-zinc-500 tracking-widest uppercase mb-2">Tipo de proveedor *</div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { key: 'talent', label: 'Talent / Influencer', desc: 'OC permanente · Solo factura a DAZZLE MGMT' },
            { key: 'mixed', label: 'Mixed', desc: 'OC permanente + OC proyecto · Todas las empresas' },
            { key: 'general', label: 'Proveedor general', desc: 'Usa el OC del proyecto en cada factura · Todas las empresas' },
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
                <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Crear OC permanente</div>
                <div className="text-[10px] text-zinc-500">Solo factura a DAZZLE MGMT &middot; OC asignado automáticamente al registrarse via NIF</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2.5 mb-3">
              <div>
                <label className={labelCls}>Nombre del talent <span className="text-amber-500">*</span></label>
                <input value={talentName} onChange={e => setTalentName(e.target.value)} placeholder="@mariagomez" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>NIF / DNI</label>
                <input value={talentNif} onChange={e => setTalentNif(e.target.value)} placeholder="12345678A" className={inputCls} />
                <div className="text-[9px] text-zinc-600 mt-0.5">Para el matching automático al registrarse</div>
              </div>
              <div>
                <label className={labelCls}>Empresa</label>
                <input value="DAZZLE MGMT" disabled className="w-full bg-zinc-700 border border-zinc-700 text-zinc-500 text-xs px-3 py-2.5 rounded cursor-not-allowed" />
              </div>
            </div>

            <div className="grid grid-cols-[1fr_2fr] gap-2.5 mb-3">
              <div>
                <label className={labelCls}>Código OC <span className="text-amber-500">*</span></label>
                <input value={talentOC} onChange={e => setTalentOC(e.target.value)} placeholder="OC-MGMTINT2026047" className={`${inputCls} font-mono`} />
                <div className="text-[9px] text-zinc-600 mt-0.5">Número secuencial de contabilidad</div>
              </div>
              {talentNif && talentOC && (
                <div className="flex items-end pb-0.5">
                  <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] flex items-start gap-2 flex-1">
                    <Shield size={13} className="flex-shrink-0 mt-0.5" />
                    Al registrarse con NIF {talentNif} el sistema asigna {talentOC} automáticamente
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleCreateOC}
                disabled={creatingOC || !talentName.trim() || !talentOC.trim()}
                className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-[13px] px-4 py-2 rounded transition-colors disabled:opacity-50"
              >
                {creatingOC ? 'Creando...' : 'Crear OC →'}
              </button>
            </div>
          </div>

          {/* Step 2: Send invitation */}
          <div className={`bg-zinc-900 border border-zinc-800 rounded-md p-4 transition-opacity ${!ocCreated ? 'opacity-40 pointer-events-none' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-7 h-7 bg-amber-500 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm text-zinc-950 flex-shrink-0">2</div>
              <div>
                <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Enviar invitación por email</div>
                <div className="text-[10px] text-zinc-500">El proveedor crea su propia contraseña durante el registro</div>
              </div>
            </div>

            <form onSubmit={handleInvite}>
              <div className="grid grid-cols-2 gap-2.5 mb-3">
                <div>
                  <label className={labelCls}>Email <span className="text-amber-500">*</span></label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="talent@email.com" required className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>Nombre</label>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder={talentName || 'Nombre del proveedor'} className={inputCls} />
                </div>
              </div>

              <div className="mb-3">
                <label className={labelCls}>Mensaje personalizado</label>
                <input value={message} onChange={e => setMessage(e.target.value)} placeholder="Hola, aquí tienes tu acceso al portal de proveedores..." className={inputCls} />
              </div>

              <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] mb-3 flex items-start gap-2">
                <Shield size={13} className="flex-shrink-0 mt-0.5" />
                El proveedor necesitará: NIF/CIF, IBAN y certificado de titularidad bancaria en PDF. Crea su propia contraseña. Link válido 72h.
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={sending || !email.trim() || !name.trim()}
                  className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-[13px] px-4 py-2 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <Send size={13} />
                  {sending ? 'Enviando...' : 'Enviar invitación'}
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
              <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Enviar invitación por email</div>
              <div className="text-[10px] text-zinc-500">Los proveedores generales no tienen OC fijo — usan el OC del proyecto en cada factura</div>
            </div>
          </div>

          <form onSubmit={handleInvite}>
            <div className="grid grid-cols-2 gap-2.5 mb-3">
              <div>
                <label className={labelCls}>Nombre / razón social <span className="text-amber-500">*</span></label>
                <input value={name} onChange={e => setName(e.target.value)} placeholder="Audiovisual Pérez SL" required className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Email <span className="text-amber-500">*</span></label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="contacto@empresa.com" required className={inputCls} />
              </div>
            </div>

            <div className="mb-3">
              <label className={labelCls}>Mensaje personalizado</label>
              <textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="Hola, te invitamos a registrarte como proveedor de DAZZ Creative..." className={`${inputCls} resize-none`} rows={2} />
            </div>

            <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[11px] mb-3 flex items-start gap-2">
              <Shield size={13} className="flex-shrink-0 mt-0.5" />
              El proveedor necesitará: NIF/CIF, IBAN y certificado de titularidad bancaria en PDF. Crea su propia contraseña. Link válido 72h.
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={sending || !name.trim() || !email.trim()}
                className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-[13px] px-4 py-2 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <Send size={13} />
                {sending ? 'Enviando...' : 'Enviar invitación'}
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
