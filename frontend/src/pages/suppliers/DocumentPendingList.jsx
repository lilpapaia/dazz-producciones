import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, Users, AlertCircle } from 'lucide-react';
import { getPendingSuppliers, getLegalDocumentStats } from '../../services/suppliersApi';

const DocumentPendingList = () => {
  const { docId } = useParams();
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState(null);
  const [docInfo, setDocInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getPendingSuppliers(docId)
      .then(r => setSuppliers(r.data))
      .catch(() => setError('Error al cargar proveedores pendientes'));
    getLegalDocumentStats()
      .then(r => {
        const doc = r.data.find(d => d.id === parseInt(docId));
        if (doc) setDocInfo(doc);
      })
      .catch(() => {});
  }, [docId]);

  if (!suppliers && !error) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
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
          <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">Pendientes de aceptar</h1>
          {docInfo && (
            <div className="text-[11px] text-zinc-500">{docInfo.title} v{docInfo.version}</div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-md p-2.5 text-xs mb-3 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Info */}
      <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded p-3 text-[12px] mb-4 flex items-start gap-2">
        <Users size={14} className="flex-shrink-0 mt-0.5" />
        <span>
          {suppliers?.length || 0} proveedor(es) no han aceptado este documento. Pueden aceptarlo desde su portal.
        </span>
      </div>

      {/* List */}
      {suppliers && suppliers.length > 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
          {/* Desktop header */}
          <div className="hidden sm:grid grid-cols-[1fr_120px_120px_120px] gap-2 px-4 py-2 border-b border-zinc-800 text-[11px] text-zinc-500 tracking-widest uppercase">
            <span>Nombre</span>
            <span>NIF</span>
            <span>OC</span>
            <span>Registro</span>
          </div>

          {suppliers.map((s, i) => (
            <div
              key={s.id}
              onClick={() => navigate(`/suppliers/${s.id}`)}
              className={`grid grid-cols-1 sm:grid-cols-[1fr_120px_120px_120px] gap-1 sm:gap-2 px-4 py-3 cursor-pointer hover:bg-zinc-800/50 transition-colors ${
                i < suppliers.length - 1 ? 'border-b border-zinc-800/50' : ''
              }`}
            >
              <div className="text-[13px] text-zinc-200 font-medium truncate">{s.name}</div>
              <div className="text-[12px] text-zinc-400 font-['IBM_Plex_Mono']">{s.nif_cif || '—'}</div>
              <div className="text-[12px] text-purple-400 font-['IBM_Plex_Mono']">{s.oc_number || '—'}</div>
              <div className="text-[12px] text-zinc-500">
                {new Date(s.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}
              </div>
            </div>
          ))}
        </div>
      ) : suppliers && suppliers.length === 0 ? (
        <div className="text-center py-12">
          <Users size={24} className="text-green-400 mx-auto mb-2" />
          <p className="text-[13px] text-zinc-400">Todos los proveedores han aceptado este documento.</p>
        </div>
      ) : null}
    </div>
  );
};

export default DocumentPendingList;
