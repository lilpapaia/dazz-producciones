import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileCheck, CheckCircle, AlertCircle, ChevronRight, Info } from 'lucide-react';
import { getBossContracts } from '../../services/suppliersApi';

const DocBadge = ({ version, accepted, readOnly }) => {
  if (!version) return <span className="text-[11px] text-zinc-600">—</span>;
  return (
    <span className={`text-[11px] inline-flex items-center gap-1 ${readOnly ? 'text-zinc-500' : accepted ? 'text-green-400' : 'text-amber-400'}`}>
      v{version}
      {accepted ? <CheckCircle size={11} /> : <AlertCircle size={11} />}
      {accepted ? 'Aceptado' : 'Pendiente'}
    </span>
  );
};

const BossContracts = () => {
  const navigate = useNavigate();
  const [influencers, setInfluencers] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getBossContracts()
      .then(r => setInfluencers(r.data))
      .catch(() => setError('Error al cargar influencers'));
  }, []);

  if (!influencers && !error) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-[47rem] mx-auto">
      <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-1">Contratos influencers</h1>
      <p className="text-[12px] text-zinc-500 mb-4">Gestiona los contratos de tus influencers</p>

      {/* Info banner */}
      <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded p-3 text-[12px] mb-4 flex items-start gap-2">
        <Info size={14} className="flex-shrink-0 mt-0.5" />
        <span>Privacidad y declaración responsable son documentos globales — solo el administrador puede actualizarlos.</span>
      </div>

      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-3 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Influencer list */}
      <div className="space-y-3">
        {influencers?.map(inf => (
          <div key={inf.id} className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            {/* Header */}
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-full bg-purple-400/10 flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400 font-['Bebas_Neue'] text-sm">
                  {inf.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium text-zinc-200 truncate">{inf.name}</div>
                <div className="text-[10px] text-zinc-500 flex gap-2">
                  {inf.oc_number && <span className="text-purple-400 font-['IBM_Plex_Mono']">{inf.oc_number}</span>}
                  {inf.nif_cif && <span>{inf.nif_cif}</span>}
                </div>
              </div>
            </div>

            {/* Document statuses */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-zinc-800/50 rounded p-2.5">
                <div className="text-[10px] text-zinc-500 tracking-widest uppercase mb-1">Contrato</div>
                <DocBadge version={inf.contract_version} accepted={inf.contract_accepted} />
                {inf.contract_type && (
                  <div className="text-[10px] text-zinc-600 mt-0.5">
                    {inf.contract_type === 'custom' ? 'Personalizado' : 'Genérico'}
                  </div>
                )}
              </div>
              <div className="bg-zinc-800/50 rounded p-2.5">
                <div className="text-[10px] text-zinc-500 tracking-widest uppercase mb-1">Autocontrol</div>
                <DocBadge version={inf.autocontrol_version} accepted={inf.autocontrol_accepted} />
              </div>
              <div className="bg-zinc-800/50 rounded p-2.5 opacity-60">
                <div className="text-[10px] text-zinc-600 tracking-widest uppercase mb-1">Privacidad</div>
                <DocBadge version={inf.privacy_version} accepted={inf.privacy_accepted} readOnly />
              </div>
              <div className="bg-zinc-800/50 rounded p-2.5 opacity-60">
                <div className="text-[10px] text-zinc-600 tracking-widest uppercase mb-1">Declaración</div>
                <DocBadge version={inf.declaration_version} accepted={inf.declaration_accepted} readOnly />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/suppliers/documents/update/CONTRACT')}
                className="text-[12px] text-amber-400 hover:text-amber-300 border border-amber-500/30 px-3 py-1.5 rounded transition-colors flex items-center gap-1"
              >
                Actualizar contrato <ChevronRight size={12} />
              </button>
              <button
                onClick={() => navigate('/suppliers/documents/update/AUTOCONTROL')}
                className="text-[12px] text-zinc-400 hover:text-zinc-200 border border-zinc-700 px-3 py-1.5 rounded transition-colors flex items-center gap-1"
              >
                Actualizar autocontrol <ChevronRight size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {influencers?.length === 0 && (
        <div className="text-center py-12 text-zinc-500 text-sm">
          No hay influencers asignados a tu empresa.
        </div>
      )}
    </div>
  );
};

export default BossContracts;
