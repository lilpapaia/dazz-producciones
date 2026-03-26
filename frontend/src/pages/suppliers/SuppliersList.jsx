import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Mic } from 'lucide-react';
import { getSuppliers } from '../../services/suppliersApi';
import { showError } from '../../utils/toast';
import useVoiceSearch from '../../hooks/useVoiceSearch';
import useClickOutside from '../../hooks/useClickOutside';

const STATUS_BADGE = {
  ACTIVE: 'bg-green-400/10 text-green-400 border border-green-400/20',
  NEW: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  DEACTIVATED: 'bg-zinc-700/50 text-zinc-500 border border-zinc-700',
};

const timeAgo = (dateStr) => {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z').getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d`;
  return `${Math.floor(days / 30)}mo`;
};

const SuppliersList = () => {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);

  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => { setSearch(transcript); setShowSuggestions(false); }, []),
  });
  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));

  const handleSearchChange = (value) => { setSearch(value); setShowSuggestions(value.length > 0); };
  const clearSearch = () => { setSearch(''); setShowSuggestions(false); };
  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches_suppliers', JSON.stringify(updated));
  };

  const load = () => {
    const params = {};
    if (statusFilter) params.status = statusFilter;
    getSuppliers(params)
      .then((s) => { setSuppliers(s.data); })
      .catch(() => showError('Error al cargar proveedores'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { setLoading(true); load(); }, [statusFilter]);
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches_suppliers');
    if (saved) try { setRecentSearches(JSON.parse(saved)); } catch { /* corrupted */ }
  }, []);

  const filtered = suppliers.filter(s => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || (s.nif_cif || '').toLowerCase().includes(q);
  });

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100">Proveedores</h1>
        <button onClick={() => navigate('/suppliers/invite')} className="bg-amber-500 hover:bg-amber-400 text-zinc-950 text-[13px] font-semibold px-4 py-2 rounded transition-colors">
          + Invitar
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2.5 mb-2 flex-wrap items-center">
        <div className="relative w-full sm:w-[300px]" ref={searchRef}>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-zinc-500 pointer-events-none" size={14} />
            <input
              type="text"
              placeholder="Buscar por nombre o NIF..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => (search || recentSearches.length > 0) && setShowSuggestions(true)}
              onKeyDown={(e) => { if (e.key === 'Enter' && search.trim()) { saveRecentSearch(search); setShowSuggestions(false); } }}
              className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 text-[13px] pl-9 pr-14 py-2 rounded-sm focus:border-amber-500 outline-none"
            />
            <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
              {search && (
                <button onClick={clearSearch} className="p-1 hover:bg-zinc-800 rounded-sm transition-colors" title="Limpiar búsqueda">
                  <X size={14} className="text-zinc-500" />
                </button>
              )}
              <button onClick={startVoiceSearch} disabled={isListening}
                className={`p-1 rounded-sm transition-colors ${isListening ? 'bg-red-500 text-white animate-pulse' : 'hover:bg-zinc-800 text-zinc-500'}`}
                title="Búsqueda por voz">
                <Mic size={14} />
              </button>
            </div>
          </div>
          {showSuggestions && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded shadow-xl max-h-64 overflow-y-auto z-50">
              {search && (() => {
                const hits = suppliers.filter(s => {
                  const q = search.toLowerCase();
                  return s.name.toLowerCase().includes(q) || (s.nif_cif || '').toLowerCase().includes(q);
                }).slice(0, 5);
                return hits.length > 0 ? (
                  <>
                    <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Proveedores encontrados</div>
                    {hits.map(s => (
                      <div key={s.id} onClick={() => { setSearch(s.name); saveRecentSearch(s.name); setShowSuggestions(false); }}
                        className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-300 border-b border-zinc-800/50 last:border-0">
                        <span className="text-amber-400">{s.name}</span>
                        {s.nif_cif && <span className="text-zinc-500 font-mono ml-2">· {s.nif_cif}</span>}
                      </div>
                    ))}
                  </>
                ) : <div className="px-3 py-3 text-xs text-zinc-600 text-center">Sin resultados</div>;
              })()}
              {!search && recentSearches.length > 0 && (
                <>
                  <div className="px-3 py-1.5 text-[9px] text-zinc-500 tracking-widest uppercase border-b border-zinc-800">Búsquedas recientes</div>
                  {recentSearches.map((term, i) => (
                    <div key={i} onClick={() => { setSearch(term); setShowSuggestions(false); }}
                      className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs text-zinc-400 border-b border-zinc-800/50 last:border-0">
                      {term}
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
        {/* Chips estado — desktop inline */}
        <div className="hidden sm:flex gap-2 flex-wrap items-center">
          {[
            { key: '', label: 'Todos' },
            { key: 'ACTIVE', label: 'Activo' },
            { key: 'NEW', label: 'Nuevo' },
            { key: 'DEACTIVATED', label: 'Desactivado' },
          ].map(f => (
            <button key={f.key} onClick={() => setStatusFilter(f.key)}
              className={`text-[13px] px-3 py-1 rounded-full border transition-all flex-shrink-0 ${
                statusFilter === f.key
                  ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold'
                  : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
              }`}>{f.label}</button>
          ))}
        </div>
      </div>

      {/* Chips estado — solo móvil, scrollable pegada a bordes */}
      <div className="sm:hidden flex gap-2 overflow-x-auto mb-3.5 -mx-4 px-4"
        style={{scrollbarWidth:'none', msOverflowStyle:'none'}}>
        {[
          { key: '', label: 'Todos' },
          { key: 'ACTIVE', label: 'Activo' },
          { key: 'NEW', label: 'Nuevo' },
          { key: 'DEACTIVATED', label: 'Desactivado' },
        ].map(f => (
          <button key={f.key} onClick={() => setStatusFilter(f.key)}
            className={`text-[13px] px-3 py-1 rounded-full border transition-all flex-shrink-0 ${
              statusFilter === f.key
                ? 'bg-amber-500 text-zinc-950 border-amber-500 font-semibold'
                : 'border-zinc-700 text-zinc-400'
            }`}>{f.label}</button>
        ))}
      </div>

      {/* CARDS — solo móvil */}
      <div className="lg:hidden flex flex-col gap-2 mb-4">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-xs text-zinc-600">No se encontraron proveedores</div>
        ) : filtered.map(s => (
          <div key={s.id} onClick={() => navigate(`/suppliers/${s.id}`)}
            className="bg-zinc-900 border border-zinc-800 rounded-md p-3.5 flex items-center gap-3 cursor-pointer active:border-amber-500 transition-colors">
            <div className="w-9 h-9 rounded-lg bg-amber-500 flex items-center justify-center font-['Bebas_Neue'] text-base text-zinc-950 flex-shrink-0">
              {s.name.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[13px] font-medium text-zinc-200 truncate">{s.name}</span>
                {(s.pending_invoices > 0 || s.has_pending_actions) && <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] text-zinc-500 font-mono">{s.nif_cif || '—'}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${STATUS_BADGE[s.status] || STATUS_BADGE.NEW}`}>{s.status}</span>
                {s.oc_number && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15">{s.oc_number}</span>
                )}
              </div>
            </div>
            <span className="text-[11px] text-zinc-600 flex-shrink-0">{timeAgo(s.last_activity)}</span>
          </div>
        ))}
      </div>

      {/* TABLE — solo desktop */}
      <div className="hidden lg:block bg-zinc-900 border border-zinc-800 rounded-md overflow-x-auto">
        <table className="w-full min-w-[700px]">
          <thead>
            <tr>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium w-5"></th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Proveedor</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">NIF/CIF</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Estado</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">OC Permanente</th>
              <th className="bg-zinc-800 px-3 py-2.5 text-left text-[11px] text-zinc-400 tracking-widest uppercase font-medium">Últ. actividad</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(s => (
              <tr key={s.id} onClick={() => navigate(`/suppliers/${s.id}`)} className="cursor-pointer hover:bg-white/[.02] transition-colors">
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  {(s.pending_invoices > 0 || s.has_pending_actions) && <div className="w-2 h-2 rounded-full bg-amber-500" />}
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <div className="text-[13px] font-medium text-zinc-200">{s.name}</div>
                  <div className="text-[11px] text-zinc-500">{s.email}</div>
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04] text-[13px] text-zinc-400 font-mono">{s.nif_cif || '—'}</td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${STATUS_BADGE[s.status] || STATUS_BADGE.NEW}`}>{s.status}</span>
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04]">
                  {s.oc_number ? (
                    <span className="text-[11px] px-1.5 py-0.5 rounded bg-amber-500/[.08] text-amber-400 font-semibold font-mono border border-amber-500/15">{s.oc_number}</span>
                  ) : <span className="text-[13px] text-zinc-600">—</span>}
                </td>
                <td className="px-3 py-2.5 border-b border-white/[.04] text-[13px] text-zinc-500">{timeAgo(s.last_activity)}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan="6" className="text-center py-8 text-xs text-zinc-600">No se encontraron proveedores</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SuppliersList;
