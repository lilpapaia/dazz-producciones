import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, CheckCircle, Shield, AlertTriangle, FileText, Upload, Eye, Code, Loader2 } from 'lucide-react';
import { inviteSupplier, createOC, checkOcNif, extractLegalDocText, inviteWithContract } from '../../services/suppliersApi';
import OCSelector from '../../components/OCSelector';
import { getCompanies } from '../../services/api';

const SupplierInvite = () => {
  const navigate = useNavigate();
  const [withOC, setWithOC] = useState(false);
  const [companies, setCompanies] = useState([]);

  // OC fields (optional step 1)
  const [talentName, setTalentName] = useState('');
  const [talentNif, setTalentNif] = useState('');
  const [nifWarning, setNifWarning] = useState('');
  const [talentOC, setTalentOC] = useState('');
  const [mgmtCompanyId, setMgmtCompanyId] = useState(null);
  const [ocCreated, setOcCreated] = useState(false);

  // Invite fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  // Personalized contract (optional, only when OC created)
  const [withContract, setWithContract] = useState(false);
  const [contractFile, setContractFile] = useState(null);
  const [contractHtml, setContractHtml] = useState('');
  const [extractingContract, setExtractingContract] = useState(false);
  const [showContractRaw, setShowContractRaw] = useState(false);
  const contractFileRef = useRef(null);

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

  const handleContractFile = async (f) => {
    if (!f || f.type !== 'application/pdf') { setError('Solo PDF'); return; }
    if (f.size > 10 * 1024 * 1024) { setError('Máximo 10MB'); return; }
    setContractFile(f);
    setError('');
    setExtractingContract(true);
    try {
      const { data } = await extractLegalDocText(f);
      setContractHtml(data.html);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al extraer texto del contrato');
      setContractFile(null);
    }
    setExtractingContract(false);
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    setError('');
    setSending(true);
    try {
      if (withContract && contractFile && contractHtml) {
        // Use invite-with-contract endpoint. Backend uses is_influencer to choose
        // INFLUENCER_CONTRACT vs SUPPLIER_CONTRACT for the personalized doc.
        const form = new FormData();
        form.append('file', contractFile);
        await inviteWithContract(form, {
          name: name.trim(),
          email: email.trim(),
          message: message.trim() || undefined,
          contract_content: contractHtml,
          is_influencer: withOC,
        });
      } else {
        await inviteSupplier({ name: name.trim(), email: email.trim(), message: message.trim() || undefined });
      }
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al enviar invitación');
    } finally {
      setSending(false);
    }
  };

  const reset = () => {
    setWithOC(false);
    setTalentName(''); setTalentNif(''); setTalentOC('');
    setOcCreated(false);
    setName(''); setEmail(''); setMessage('');
    setWithContract(false); setContractFile(null); setContractHtml('');
    setSent(false); setError('');
  };

  // ─── SUCCESS STATE ───
  if (sent) {
    return (
      <div className="max-w-[47rem] mx-auto mt-12">
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
  const labelCls = "text-[12px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  // Can show invite form directly (no OC) or after OC created
  const canShowInviteForm = !withOC || ocCreated;

  return (
    <div className="max-w-[47rem] mx-auto">
      <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-4">Invitar proveedor</h1>

      {/* Info bar */}
      <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-3 text-[13px] mb-4 leading-relaxed">
        El proveedor recibe un link único seguro (72h) para registrarse — rellena todos sus datos, sube el certificado bancario y crea su propia contraseña.
      </div>

      {/* OC toggle */}
      <div className="mb-4">
        <label className="flex items-center gap-3 cursor-pointer bg-zinc-900 border border-zinc-800 rounded-md p-3.5 hover:border-zinc-700 transition-colors">
          <input
            type="checkbox"
            checked={withOC}
            onChange={e => { setWithOC(e.target.checked); setOcCreated(false); setError(''); }}
            className="w-4 h-4 accent-amber-500 rounded"
          />
          <div>
            <div className="text-[13px] text-zinc-200 font-medium">Crear OC permanente</div>
            <div className="text-[12px] text-zinc-500">Asignar un código OC fijo que se vincula automáticamente al registrarse via NIF</div>
          </div>
        </label>
      </div>

      {/* ─── OC CREATION (optional step 1) ─── */}
      {withOC && (
        <div className={`bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3 transition-opacity ${ocCreated ? 'opacity-40 pointer-events-none' : ''}`}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm flex-shrink-0 ${ocCreated ? 'bg-zinc-700 text-green-400' : 'bg-amber-500 text-zinc-950'}`}>
              {ocCreated ? '✓' : '1'}
            </div>
            <div>
              <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Crear OC permanente</div>
              <div className="text-[12px] text-zinc-500">OC asignado automáticamente al registrarse via NIF</div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-3">
            <div>
              <label className={labelCls}>Nombre del proveedor <span className="text-amber-500">*</span></label>
              <input value={talentName} onChange={e => setTalentName(e.target.value)} placeholder="@mariagomez o Empresa SL" className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>NIF / DNI</label>
              <input value={talentNif} onChange={e => { setTalentNif(e.target.value); setNifWarning(''); }}
                onBlur={async () => {
                  if (!talentNif.trim()) return;
                  try {
                    const { data } = await checkOcNif(talentNif.trim());
                    if (data.exists) setNifWarning(`Ya existe un OC (${data.oc_number}) con este NIF — verifica que no es un duplicado`);
                  } catch {}
                }}
                placeholder="12345678A" className={inputCls} />
              {nifWarning ? (
                <div className="text-[11px] text-amber-400 mt-1 flex items-center gap-1"><AlertTriangle size={11} /> {nifWarning}</div>
              ) : (
                <div className="text-[12px] text-zinc-600 mt-0.5">Para el matching automático al registrarse</div>
              )}
            </div>
            <div>
              <label className={labelCls}>Empresa</label>
              <select value={mgmtCompanyId || ''} onChange={e => setMgmtCompanyId(e.target.value ? parseInt(e.target.value) : null)} className={inputCls}>
                <option value="">Seleccionar empresa</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[1fr_2fr] gap-2.5 mb-3">
            <div>
              <label className={labelCls}>Código OC <span className="text-amber-500">*</span></label>
              <OCSelector permanentOnly onSelect={oc => setTalentOC(oc)} onClear={() => setTalentOC('')} />
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
      )}

      {/* ─── PERSONALIZED CONTRACT (optional, available for both flows) ─── */}
      {canShowInviteForm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3">
          <label className="flex items-center gap-3 cursor-pointer mb-3">
            <input
              type="checkbox"
              checked={withContract}
              onChange={e => { setWithContract(e.target.checked); if (!e.target.checked) { setContractFile(null); setContractHtml(''); } }}
              className="w-4 h-4 accent-amber-500 rounded"
            />
            <div>
              <div className="text-[13px] text-zinc-200 font-medium">
                Adjuntar contrato personalizado de {withOC ? 'influencer' : 'proveedor'}
              </div>
              <div className="text-[12px] text-zinc-500">Si no adjuntas, se usará el contrato genérico vigente</div>
            </div>
          </label>

          {withContract && (
            <div className="ml-7">
              {!contractFile ? (
                <div
                  onClick={() => contractFileRef.current?.click()}
                  className="border-2 border-dashed border-zinc-700 rounded-lg p-4 text-center cursor-pointer hover:border-amber-500/50 transition-colors"
                >
                  <Upload size={20} className="text-zinc-600 mx-auto mb-1" />
                  <p className="text-[12px] text-zinc-400">Subir PDF del contrato</p>
                  <input ref={contractFileRef} type="file" accept=".pdf" onChange={e => { if (e.target.files?.[0]) handleContractFile(e.target.files[0]); e.target.value = ''; }} className="hidden" />
                </div>
              ) : (
                <div>
                  <div className="flex items-center gap-2 bg-zinc-800 rounded p-2 mb-2">
                    <FileText size={13} className="text-amber-400" />
                    <span className="text-[12px] text-zinc-300 flex-1 truncate">{contractFile.name}</span>
                    {!extractingContract && (
                      <button onClick={() => { setContractFile(null); setContractHtml(''); }} className="text-zinc-500 hover:text-zinc-300 text-[11px]">
                        Cambiar
                      </button>
                    )}
                  </div>
                  {extractingContract && (
                    <div className="flex items-center gap-2 text-amber-400 text-[11px] mb-2">
                      <Loader2 size={12} className="animate-spin" /> Extrayendo texto con IA...
                    </div>
                  )}
                  {contractHtml && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-zinc-500">Preview del contrato</span>
                        <button onClick={() => setShowContractRaw(!showContractRaw)} className="text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-1">
                          {showContractRaw ? <><Eye size={10} /> Preview</> : <><Code size={10} /> HTML</>}
                        </button>
                      </div>
                      {showContractRaw ? (
                        <textarea
                          value={contractHtml}
                          onChange={e => setContractHtml(e.target.value)}
                          className="w-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-[10px] font-['IBM_Plex_Mono'] p-2 rounded h-[150px] resize-y focus:border-amber-500 outline-none"
                        />
                      ) : (
                        <div className="bg-zinc-950 border border-zinc-800 rounded p-3 max-h-[200px] overflow-y-auto">
                          <div dangerouslySetInnerHTML={{ __html: contractHtml }} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ─── INVITE FORM ─── */}
      <div className={`bg-zinc-900 border border-zinc-800 rounded-md p-4 transition-opacity ${withOC && !ocCreated ? 'opacity-40 pointer-events-none' : ''}`}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-7 h-7 bg-amber-500 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm text-zinc-950 flex-shrink-0">
            {withOC ? '2' : '1'}
          </div>
          <div>
            <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Enviar invitación por email</div>
            <div className="text-[12px] text-zinc-500">El proveedor crea su propia contraseña durante el registro</div>
          </div>
        </div>

        <form onSubmit={handleInvite}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-3">
            <div>
              <label className={labelCls}>Nombre / razón social <span className="text-amber-500">*</span></label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder={withOC && talentName ? talentName : 'Audiovisual Pérez SL'} required className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>Email <span className="text-amber-500">*</span></label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="contacto@empresa.com" required className={inputCls} />
            </div>
          </div>

          <div className="mb-3">
            <label className={labelCls}>Mensaje personalizado</label>
            <input value={message} onChange={e => setMessage(e.target.value)} placeholder="Hola, te invitamos a registrarte como proveedor de DAZZ Creative..." className={inputCls} />
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
