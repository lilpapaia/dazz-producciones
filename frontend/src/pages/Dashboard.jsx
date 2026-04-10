import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects, getCompanies } from '../services/api';
import { Plus, Search, X, Mic, Clock, Building2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import useVoiceSearch from '../hooks/useVoiceSearch';
import useClickOutside from '../hooks/useClickOutside';
import { ROLES } from '../constants/roles';

// ── Tarjeta de proyecto (hoisted — avoids remount on every Dashboard render) ──
const ProjectCard = ({ project, navigate, activeTab, companies }) => (
  <div
    onClick={() => navigate(`/projects/${project.id}`)}
    className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-4 cursor-pointer transition-all hover:shadow-lg hover:shadow-amber-500/10"
  >
    <div className="flex items-center justify-between gap-2 mb-3">
      <h3 className="text-lg font-bebas tracking-wider">{project.creative_code}</h3>
      <StatusBadge type="project" value={project.status} />
    </div>

    <p className="text-sm text-zinc-300 mb-3 line-clamp-2">{project.description}</p>

    <div className="flex items-center gap-2 text-sm text-zinc-500 mb-2 flex-wrap">
      <div className="flex items-center gap-1">
        <span>👤</span>
        <span>{project.responsible}</span>
      </div>
      <span>•</span>
      <div className="flex items-center gap-1">
        <span>📅</span>
        <span>{project.year}</span>
      </div>
      <span>•</span>
      <div className="flex items-center gap-1">
        <span>🎫</span>
        <span>{project.tickets_count} tickets</span>
      </div>
    </div>

    {activeTab === 'all' && companies.length > 1 && (
      <div className="flex items-center gap-2 text-sm text-zinc-400 mb-3">
        <Building2 size={13} className="text-zinc-500" />
        <span>{project.owner_company?.name || project.company || 'Sin empresa'}</span>
      </div>
    )}

    <div className="pt-3 border-t border-zinc-800">
      <p className="text-sm text-zinc-500">
        IMPORTE TOTAL <span className="text-amber-500 font-bold text-2xl ml-2">| {project.total_amount?.toFixed(2)}€</span>
      </p>
    </div>
  </div>
);

// ── Barra de búsqueda + filtros (hoisted) ──
const SearchAndFilters = ({
  stats, statusFilter, setStatusFilter, searchTerm, handleSearchChange,
  showSuggestions, suggestions, navigate, saveRecentSearch, recentSearches,
  setSearchTerm, setShowSuggestions, clearSearch, handleSearchSubmit,
  startVoiceSearch, isListening, searchRef,
}) => (
  <div className="flex flex-col md:flex-row md:items-center gap-4">
    <div className="flex gap-2 overflow-x-auto">
      {[
        { key: 'all', label: 'TODOS', count: stats.total },
        { key: 'en_curso', label: 'EN CURSO', count: stats.activos },
        { key: 'cerrado', label: 'CERRADOS', count: stats.cerrados },
      ].map(f => (
        <button
          key={f.key}
          onClick={() => setStatusFilter(f.key)}
          className={`px-4 py-2 text-sm font-semibold rounded-sm transition-colors whitespace-nowrap ${
            statusFilter === f.key
              ? 'bg-amber-500 text-zinc-950'
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
          }`}
        >
          {f.label} ({f.count})
        </button>
      ))}
    </div>

    <div className="w-full md:w-96 relative md:ml-auto" ref={searchRef}>
      <div className="relative">
        <Search className="absolute left-3 top-2.5 text-zinc-500" size={18} />
        <input
          type="search"
          placeholder=" Buscar proyectos..."
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
          onFocus={() => searchTerm && setShowSuggestions(true)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
          className="w-full px-3 py-2 pl-10 pr-20 bg-zinc-900 border border-zinc-700 rounded-sm text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-amber-500 transition-colors"
        />
        <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5">
          {searchTerm && (
            <button onClick={clearSearch} className="p-1 hover:bg-zinc-800 rounded-sm transition-colors" title="Limpiar búsqueda">
              <X size={16} className="text-zinc-500" />
            </button>
          )}
          <button
            onClick={startVoiceSearch}
            disabled={isListening}
            className={`p-1 rounded-sm transition-colors ${isListening ? 'bg-red-500 text-white animate-pulse' : 'hover:bg-zinc-800 text-zinc-500'}`}
            title="Búsqueda por voz"
          >
            <Mic size={16} />
          </button>
        </div>
      </div>

      {showSuggestions && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-96 overflow-y-auto z-50">
          {searchTerm && suggestions.length > 0 && (
            <div>
              <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800">
                PROYECTOS ENCONTRADOS
              </div>
              {suggestions.map((project) => (
                <div
                  key={project.id}
                  onClick={() => { navigate(`/projects/${project.id}`); saveRecentSearch(searchTerm); }}
                  className="px-3 py-2.5 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{project.creative_code}</p>
                      <p className="text-xs text-zinc-400 mt-0.5">{project.description}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                        <span>👤 {project.responsible}</span>
                        <span>📅 {project.year}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-amber-500 font-bold text-sm">{project.total_amount?.toFixed(2)}€</p>
                      <p className="text-xs text-zinc-500">{project.tickets_count} tickets</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {searchTerm && suggestions.length === 0 && (
            <div className="px-4 py-6 text-center text-zinc-500">
              <p className="text-sm">No se encontraron proyectos</p>
            </div>
          )}
          {!searchTerm && recentSearches.length > 0 && (
            <div>
              <div className="px-3 py-1.5 text-xs text-zinc-500 font-mono border-b border-zinc-800 flex items-center gap-2">
                <Clock size={12} />
                BÚSQUEDAS RECIENTES
              </div>
              {recentSearches.map((term, index) => (
                <div
                  key={index}
                  onClick={() => { setSearchTerm(term); setShowSuggestions(true); }}
                  className="px-3 py-2 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0 flex items-center gap-2"
                >
                  <Search size={12} className="text-zinc-600" />
                  <span className="text-sm text-zinc-300">{term}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === ROLES.ADMIN;

  const [projects, setProjects] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [companiesError, setCompaniesError] = useState(false);
  const [projectsError, setProjectsError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  // Tab activa — 'all' o company.id
  const [activeTab, setActiveTab] = useState('all');

  // Búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);

  const { isListening, startVoiceSearch } = useVoiceSearch({
    lang: 'es-ES',
    onResult: useCallback((transcript) => {
      setSearchTerm(transcript);
      let recent = [];
      try { const saved = localStorage.getItem('recentSearches'); if (saved) recent = JSON.parse(saved); } catch { /* corrupted */ }
      const updated = [transcript, ...recent.filter(s => s !== transcript)].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
    }, []),
  });

  useClickOutside(searchRef, useCallback(() => setShowSuggestions(false), []));

  useEffect(() => {
    loadProjects();
    loadRecentSearches();
    loadCompanies();
  }, []);

  const loadProjects = async () => {
    try {
      setProjectsError(false);
      const response = await getProjects();
      setProjects(response.data);
    } catch {
      setProjectsError(true);
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      setCompaniesError(false);
      const response = await getCompanies();
      setCompanies(response.data);
    } catch {
      setCompaniesError(true);
    }
  };

  const loadRecentSearches = () => {
    try {
      const saved = localStorage.getItem('recentSearches');
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch { /* corrupted localStorage */ }
  };

  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  };

  const handleSearchChange = (value) => {
    setSearchTerm(value);
    setShowSuggestions(value.length > 0);
  };

  const handleSearchSubmit = () => {
    if (searchTerm.trim()) {
      saveRecentSearch(searchTerm);
      setShowSuggestions(false);
    }
  };

  const clearSearch = () => {
    setSearchTerm('');
    setShowSuggestions(false);
  };

  // ── Proyectos filtrados por tab (solo ADMIN) + statusFilter + searchTerm ──
  const getFilteredProjects = (tabId = activeTab) => {
    return projects
      .filter(p => {
        // Filtro por empresa (tab) — solo ADMIN
        if (isAdmin && tabId !== 'all') {
          const companyName = companies.find(c => c.id === tabId)?.name;
          return (p.owner_company?.name || p.company) === companyName;
        }
        return true;
      })
      .filter(p => {
        if (statusFilter === 'en_curso') return p.status === 'en_curso';
        if (statusFilter === 'cerrado') return p.status === 'cerrado';
        return true;
      })
      .filter(p => {
        if (!searchTerm) return true;
        const search = searchTerm.toLowerCase();
        return (
          p.creative_code.toLowerCase().includes(search) ||
          (p.description || '').toLowerCase().includes(search) ||
          p.responsible.toLowerCase().includes(search) ||
          p.year.includes(search) ||
          (p.owner_company?.name || p.company || '').toLowerCase().includes(search)
        );
      });
  };

  const filteredProjects = useMemo(() => getFilteredProjects(), [projects, activeTab, companies, statusFilter, searchTerm, isAdmin]);
  const suggestions = useMemo(() => filteredProjects.slice(0, 5), [filteredProjects]);

  // Stats por empresa para las tabs (precomputed map)
  const companyStatsMap = useMemo(() => {
    const map = {};
    companies.forEach(company => {
      const compProjects = projects.filter(p =>
        (p.owner_company?.name || p.company) === company.name
      );
      map[company.id] = {
        total: compProjects.length,
        activos: compProjects.filter(p => p.status === 'en_curso').length,
        cerrados: compProjects.filter(p => p.status === 'cerrado').length,
        importe: compProjects.reduce((sum, p) => sum + (p.total_amount || 0), 0),
      };
    });
    return map;
  }, [projects, companies]);

  const allStats = useMemo(() => ({
    total: projects.length,
    activos: projects.filter(p => p.status === 'en_curso').length,
    cerrados: projects.filter(p => p.status === 'cerrado').length,
    importe: projects.reduce((sum, p) => sum + (p.total_amount || 0), 0),
  }), [projects]);

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) return <LoadingSpinner size="lg" fullPage />;

  // ══════════════════════════════════════════════════════════════════
  // VISTA ADMIN — con tabs por empresa
  // ══════════════════════════════════════════════════════════════════
  if (isAdmin) {
    const activeStats = activeTab === 'all'
      ? allStats
      : (() => {
          return companyStatsMap[activeTab] || allStats;
        })();

    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 overflow-x-hidden">
        {/* Header sticky */}
        <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">

            {/* Título + botón nuevo proyecto */}
            <div className="flex flex-col items-center text-center gap-3 md:hidden mb-4">
              <h1 className="text-4xl font-bebas tracking-wider">TODOS LOS PROYECTOS</h1>
              <button
                onClick={() => navigate('/projects/create')}
                className="flex items-center gap-2 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
              >
                <Plus size={18} />
                NUEVO PROYECTO
              </button>
            </div>
            <div className="hidden md:flex items-start justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bebas tracking-wider mb-1">TODOS LOS PROYECTOS</h1>
                <p className="text-zinc-400 text-sm">Vista global de todas las empresas</p>
              </div>
              <button
                onClick={() => navigate('/projects/create')}
                className="flex items-center gap-2 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
              >
                <Plus size={18} />
                NUEVO PROYECTO
              </button>
            </div>

            {/* ── TABS por empresa ── */}
            {companiesError && (
              <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-[12px] flex items-center gap-2 mb-3">
                Error al cargar empresas
                <button onClick={loadCompanies} className="text-amber-500 hover:text-amber-400 ml-1 font-semibold">Reintentar</button>
              </div>
            )}

            <div className="flex gap-2 overflow-x-auto pb-1 mb-4 scrollbar-hide -mx-4 px-4 sm:-mx-6 sm:px-6">
              {/* Tab "Todas" */}
              <button
                onClick={() => setActiveTab('all')}
                className={`flex-shrink-0 flex flex-col items-start px-4 py-2.5 rounded-sm border transition-all ${
                  activeTab === 'all'
                    ? 'bg-amber-500/10 border-amber-500 text-amber-400'
                    : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <span className="text-xs font-bold tracking-wider uppercase">Todas</span>
                <div className="flex items-center gap-2 mt-1 text-xs">
                  <span className={activeTab === 'all' ? 'text-green-400' : 'text-zinc-500'}>
                    ● {allStats.activos} activos
                  </span>
                  <span className={activeTab === 'all' ? 'text-zinc-400' : 'text-zinc-600'}>
                    · {allStats.cerrados} cerrados
                  </span>
                </div>
                <span className={`text-sm font-bold mt-0.5 ${activeTab === 'all' ? 'text-amber-400' : 'text-zinc-400'}`}>
                  {allStats.importe.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, '.')}€
                </span>
              </button>

              {/* Tab por empresa */}
              {companies.map(company => {
                const stats = companyStatsMap[company.id];
                const isActive = activeTab === company.id;
                return (
                  <button
                    key={company.id}
                    onClick={() => setActiveTab(company.id)}
                    className={`flex-shrink-0 flex flex-col items-start px-4 py-2.5 rounded-sm border transition-all ${
                      isActive
                        ? 'bg-amber-500/10 border-amber-500 text-amber-400'
                        : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500'
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <Building2 size={12} className={isActive ? 'text-amber-400' : 'text-zinc-500'} />
                      <span className="text-xs font-bold tracking-wider uppercase whitespace-nowrap">
                        {company.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs">
                      <span className={isActive ? 'text-green-400' : 'text-zinc-500'}>
                        ● {stats.activos} activos
                      </span>
                      <span className={isActive ? 'text-zinc-400' : 'text-zinc-600'}>
                        · {stats.cerrados} cerrados
                      </span>
                    </div>
                    <span className={`text-sm font-bold mt-0.5 ${isActive ? 'text-amber-400' : 'text-zinc-400'}`}>
                      {stats.importe.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, '.')}€
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Filtros + búsqueda */}
            <SearchAndFilters
              stats={activeStats} statusFilter={statusFilter} setStatusFilter={setStatusFilter}
              searchTerm={searchTerm} handleSearchChange={handleSearchChange}
              showSuggestions={showSuggestions} suggestions={suggestions}
              navigate={navigate} saveRecentSearch={saveRecentSearch}
              recentSearches={recentSearches} setSearchTerm={setSearchTerm}
              setShowSuggestions={setShowSuggestions} clearSearch={clearSearch}
              handleSearchSubmit={handleSearchSubmit} startVoiceSearch={startVoiceSearch}
              isListening={isListening} searchRef={searchRef}
            />

            {/* Contador */}
            <p className="text-sm text-zinc-500 mt-3">
              Mostrando {filteredProjects.length} de {projects.length} proyectos
              {searchTerm && ` para "${searchTerm}"`}
            </p>
          </div>
        </div>

        {/* Grid proyectos */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-8">
          {projectsError && (
            <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-[12px] flex items-center gap-2 mb-4">
              Error al cargar proyectos
              <button onClick={loadProjects} className="text-amber-500 hover:text-amber-400 ml-1 font-semibold">Reintentar</button>
            </div>
          )}
          {filteredProjects.length === 0 && !projectsError ? (
            <EmptyState
              message="No hay proyectos que mostrar"
              action={searchTerm ? { label: "Limpiar búsqueda", onClick: clearSearch } : null}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProjects.map(project => (
                <ProjectCard key={project.id} project={project} navigate={navigate} activeTab={activeTab} companies={companies} />
              ))}
            </div>
          )}
        </main>
      </div>
    );
  }

  // ══════════════════════════════════════════════════════════════════
  // VISTA BOSS / WORKER — grid plano sin tabs (igual que antes)
  // ══════════════════════════════════════════════════════════════════
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 overflow-x-hidden">
      {/* Header sticky */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          {/* Móvil */}
          <div className="flex flex-col items-center text-center gap-4 md:hidden mb-6">
            <h1 className="text-4xl font-bebas tracking-wider">MIS PROYECTOS</h1>
            <p className="text-zinc-400 text-sm">Gestión de producciones activas</p>
            <button
              onClick={() => navigate('/projects/create')}
              className="flex items-center gap-2 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
            >
              <Plus size={18} />
              NUEVO PROYECTO
            </button>
          </div>
          {/* Desktop */}
          <div className="hidden md:flex items-start justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bebas tracking-wider mb-2">MIS PROYECTOS</h1>
              <p className="text-zinc-400">Gestión de producciones activas</p>
            </div>
            <button
              onClick={() => navigate('/projects/create')}
              className="flex items-center gap-2 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
            >
              <Plus size={18} />
              NUEVO PROYECTO
            </button>
          </div>

          <SearchAndFilters
              stats={allStats} statusFilter={statusFilter} setStatusFilter={setStatusFilter}
              searchTerm={searchTerm} handleSearchChange={handleSearchChange}
              showSuggestions={showSuggestions} suggestions={suggestions}
              navigate={navigate} saveRecentSearch={saveRecentSearch}
              recentSearches={recentSearches} setSearchTerm={setSearchTerm}
              setShowSuggestions={setShowSuggestions} clearSearch={clearSearch}
              handleSearchSubmit={handleSearchSubmit} startVoiceSearch={startVoiceSearch}
              isListening={isListening} searchRef={searchRef}
            />

          <p className="text-sm text-zinc-500 mt-4">
            Mostrando {filteredProjects.length} de {projects.length} proyectos
            {searchTerm && ` para "${searchTerm}"`}
          </p>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-8">
        {projectsError && (
          <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-[12px] flex items-center gap-2 mb-4">
            Error al cargar proyectos
            <button onClick={loadProjects} className="text-amber-500 hover:text-amber-400 ml-1 font-semibold">Reintentar</button>
          </div>
        )}
        {filteredProjects.length === 0 && !projectsError ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-12 text-center">
            <p className="text-zinc-400 mb-2">No hay proyectos que mostrar</p>
            {searchTerm && (
              <button onClick={clearSearch} className="text-amber-500 hover:text-amber-400 text-sm">
                Limpiar búsqueda
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map(project => (
              <ProjectCard key={project.id} project={project} navigate={navigate} activeTab={activeTab} companies={companies} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
