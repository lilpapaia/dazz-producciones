import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Upload, FileText, Eye, Code, ChevronLeft, AlertCircle, CheckCircle, Loader2, Users } from 'lucide-react';
import { extractLegalDocText, createLegalDocument, getLegalDocInfluencers, getLegalDocGeneralSuppliers, getLegalDocumentStats } from '../../services/suppliersApi';
import ConfirmDialog from '../../components/ConfirmDialog';

const TITLES = {
  PRIVACY: 'Política de Privacidad',
  TERMS: 'Condiciones de Uso',
  SUPPLIER_CONTRACT: 'Contrato de Proveedor',
  INFLUENCER_CONTRACT: 'Contrato de Influencer',
  AUTOCONTROL: 'Código de Autocontrol',
};

const PERSONALIZABLE_TYPES = new Set(['SUPPLIER_CONTRACT', 'INFLUENCER_CONTRACT']);

const UpdateDocument = () => {
  const { docType } = useParams();
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const type = docType?.toUpperCase();

  // State
  const [file, setFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [htmlContent, setHtmlContent] = useState('');
  const [showRaw, setShowRaw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [currentVersion, setCurrentVersion] = useState(null);

  // Contract-specific (INFLUENCER_CONTRACT or SUPPLIER_CONTRACT can be personalized per-supplier)
  const isPersonalizable = PERSONALIZABLE_TYPES.has(type);
  const isInfluencerContract = type === 'INFLUENCER_CONTRACT';
  const targetLabel = isInfluencerContract ? 'Influencers' : 'Proveedores';
  const [contractMode, setContractMode] = useState('generic'); // generic | custom
  const [targets, setTargets] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loadingTargets, setLoadingTargets] = useState(false);

  useEffect(() => {
    getLegalDocumentStats()
      .then(r => {
        const doc = r.data.find(d => d.type === type);
        if (doc) setCurrentVersion(doc.version);
      })
      .catch(() => {});

    if (isPersonalizable) {
      setLoadingTargets(true);
      const loader = isInfluencerContract ? getLegalDocInfluencers : getLegalDocGeneralSuppliers;
      loader()
        .then(r => setTargets(r.data))
        .catch(() => {})
        .finally(() => setLoadingTargets(false));
    }
  }, [type, isPersonalizable, isInfluencerContract]);

  const handleFile = async (f) => {
    if (!f || f.type !== 'application/pdf') { setError('Solo PDF'); return; }
    if (f.size > 10 * 1024 * 1024) { setError('Máximo 10MB'); return; }
    setFile(f);
    setError('');
    setExtracting(true);
    try {
      const { data } = await extractLegalDocText(f);
      setHtmlContent(data.html);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al extraer texto con IA');
    }
    setExtracting(false);
  };

  const handleSave = async () => {
    setConfirmOpen(false);
    setSaving(true);
    setError('');

    try {
      if (isPersonalizable && contractMode === 'custom') {
        // Create personalized contracts for each selected supplier/influencer
        for (const supplierId of selected) {
          const form = new FormData();
          form.append('file', file);
          const tgt = targets.find(t => t.id === supplierId);
          const baseTitle = TITLES[type] || type;
          await createLegalDocument(form, {
            doc_type: type,
            title: `${baseTitle} — ${tgt?.name || supplierId}`,
            content: htmlContent,
            is_generic: false,
            target_supplier_id: supplierId,
          });
        }
      } else {
        const form = new FormData();
        form.append('file', file);
        await createLegalDocument(form, {
          doc_type: type,
          title: TITLES[type] || type,
          content: htmlContent,
          is_generic: true,
        });
      }
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar documento');
    }
    setSaving(false);
  };

  const toggleTarget = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === targets.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(targets.map(t => t.id)));
    }
  };

  const newVersion = (currentVersion || 0) + 1;
  const canConfirm = file && htmlContent && !extracting && !saving &&
    (!isPersonalizable || contractMode === 'generic' || selected.size > 0);

  // Success state
  if (success) {
    return (
      <div className="max-w-[47rem] mx-auto mt-12">
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-6 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100 mb-2">Documento actualizado</h2>
          <p className="text-[13px] text-zinc-400 mb-4">
            {TITLES[type]} v{newVersion} está activo. Los proveedores aplicables deberán aceptar la nueva versión.
          </p>
          <button onClick={() => navigate('/suppliers/documents')} className="text-[13px] bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold px-4 py-2 rounded transition-colors">
            Volver a documentos
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[47rem] mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button onClick={() => navigate('/suppliers/documents')} className="w-8 h-8 bg-zinc-800 rounded-lg flex items-center justify-center">
          <ChevronLeft size={16} className="text-zinc-300" />
        </button>
        <div>
          <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">Actualizar {TITLES[type]}</h1>
          <div className="text-[11px] text-zinc-500">
            Versión actual: v{currentVersion || '?'} → Nueva: v{newVersion}
          </div>
        </div>
      </div>

      {/* Contract mode selector */}
      {isPersonalizable && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3">
          <div className="text-[12px] text-zinc-400 tracking-widest uppercase font-semibold mb-2">Alcance del contrato</div>
          <div className="flex gap-2">
            <button
              onClick={() => setContractMode('generic')}
              className={`flex-1 text-[13px] py-2.5 rounded border transition-colors ${
                contractMode === 'generic'
                  ? 'border-amber-500 bg-amber-500/10 text-amber-400'
                  : 'border-zinc-700 text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              Genérico (todos {isInfluencerContract ? 'los influencers' : 'los proveedores'})
            </button>
            <button
              onClick={() => setContractMode('custom')}
              className={`flex-1 text-[13px] py-2.5 rounded border transition-colors ${
                contractMode === 'custom'
                  ? 'border-amber-500 bg-amber-500/10 text-amber-400'
                  : 'border-zinc-700 text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              Personalizado (seleccionar)
            </button>
          </div>
        </div>
      )}

      {/* Target selection (contract custom mode) */}
      {isPersonalizable && contractMode === 'custom' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[12px] text-zinc-400 tracking-widest uppercase font-semibold">
              {targetLabel} ({selected.size}/{targets.length})
            </div>
            <button onClick={toggleAll} className="text-[11px] text-amber-400 hover:text-amber-300">
              {selected.size === targets.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
            </button>
          </div>
          {loadingTargets ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 size={16} className="text-amber-500 animate-spin" />
            </div>
          ) : (
            <div className="space-y-1 max-h-[200px] overflow-y-auto">
              {targets.map(tgt => (
                <label key={tgt.id} className="flex items-center gap-2.5 py-1.5 px-2 rounded hover:bg-zinc-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selected.has(tgt.id)}
                    onChange={() => toggleTarget(tgt.id)}
                    className="w-3.5 h-3.5 accent-amber-500 rounded"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] text-zinc-200 truncate">{tgt.name}</div>
                    <div className="text-[10px] text-zinc-500 flex gap-2">
                      {tgt.oc_number && <span className="text-purple-400 font-['IBM_Plex_Mono']">{tgt.oc_number}</span>}
                      {tgt.nif_cif && !tgt.oc_number && <span className="font-['IBM_Plex_Mono']">{tgt.nif_cif}</span>}
                      {tgt.contract_type && (
                        <span>v{tgt.contract_version} ({tgt.contract_type === 'custom' ? 'especial' : 'genérico'})</span>
                      )}
                    </div>
                  </div>
                </label>
              ))}
              {targets.length === 0 && (
                <div className="text-[12px] text-zinc-500 text-center py-4">
                  No hay {isInfluencerContract ? 'influencers' : 'proveedores generales'} registrados
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 1: Upload PDF */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3">
        <div className="flex items-center gap-3 mb-3">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm flex-shrink-0 ${file ? 'bg-zinc-700 text-green-400' : 'bg-amber-500 text-zinc-950'}`}>
            {file ? '✓' : '1'}
          </div>
          <div>
            <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Subir PDF del documento</div>
            <div className="text-[12px] text-zinc-500">La IA extraerá el texto automáticamente</div>
          </div>
        </div>

        {!file ? (
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-zinc-700 rounded-lg p-6 text-center cursor-pointer hover:border-amber-500/50 transition-colors"
          >
            <Upload size={24} className="text-zinc-600 mx-auto mb-2" />
            <p className="text-[13px] text-zinc-400">Seleccionar PDF</p>
            <p className="text-[11px] text-zinc-600">Máximo 10MB</p>
            <input ref={fileRef} type="file" accept=".pdf" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); e.target.value = ''; }} className="hidden" />
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-zinc-800 rounded p-2.5">
            <FileText size={14} className="text-amber-400" />
            <span className="text-[13px] text-zinc-300 flex-1 truncate">{file.name}</span>
            <span className="text-[11px] text-zinc-500">{(file.size / 1024).toFixed(0)} KB</span>
            {!extracting && (
              <button onClick={() => { setFile(null); setHtmlContent(''); }} className="text-zinc-500 hover:text-zinc-300 text-[11px]">
                Cambiar
              </button>
            )}
          </div>
        )}

        {extracting && (
          <div className="flex items-center gap-2 mt-3 text-amber-400 text-[12px]">
            <Loader2 size={14} className="animate-spin" /> Extrayendo texto con IA...
          </div>
        )}
      </div>

      {/* Step 2: Preview */}
      {htmlContent && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 mb-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-7 h-7 bg-amber-500 rounded-full flex items-center justify-center font-['Bebas_Neue'] text-sm text-zinc-950 flex-shrink-0">
              2
            </div>
            <div className="flex-1">
              <div className="font-['Bebas_Neue'] text-sm tracking-wide text-zinc-100">Preview y edición</div>
              <div className="text-[12px] text-zinc-500">Revisa el HTML extraído. Edita si algo quedó mal.</div>
            </div>
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-[11px] text-zinc-400 hover:text-zinc-200 border border-zinc-700 px-2.5 py-1 rounded flex items-center gap-1"
            >
              {showRaw ? <><Eye size={11} /> Preview</> : <><Code size={11} /> HTML</>}
            </button>
          </div>

          {showRaw ? (
            <textarea
              value={htmlContent}
              onChange={e => setHtmlContent(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-[11px] font-['IBM_Plex_Mono'] p-3 rounded h-[300px] resize-y focus:border-amber-500 outline-none"
            />
          ) : (
            <div className="bg-zinc-950 border border-zinc-800 rounded p-4 max-h-[400px] overflow-y-auto">
              <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-3 flex items-center gap-2">
          <AlertCircle size={13} /> {error}
        </div>
      )}

      {/* Actions */}
      {htmlContent && (
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => navigate('/suppliers/documents')}
            className="flex-1 text-[13px] py-2.5 rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={() => setConfirmOpen(true)}
            disabled={!canConfirm}
            className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold text-[13px] py-2.5 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : null}
            {saving ? 'Guardando...' : `Publicar v${newVersion}`}
          </button>
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleSave}
        title={`Actualizar ${TITLES[type]}`}
        message={
          isPersonalizable && contractMode === 'custom'
            ? `Se creará un contrato personalizado v${newVersion} para ${selected.size} ${isInfluencerContract ? 'influencer' : 'proveedor'}(es). Los seleccionados deberán aceptar la nueva versión.`
            : `¿Actualizar ${TITLES[type]} a v${newVersion}? Todos los proveedores aplicables deberán aceptar de nuevo.`
        }
        type="warning"
        confirmText="Publicar"
      />
    </div>
  );
};

export default UpdateDocument;
