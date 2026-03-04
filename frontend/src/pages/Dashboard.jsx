import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects } from '../services/api';
import { Plus, Search, X, Mic, Clock } from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [isListening, setIsListening] = useState(false);
  
  const searchRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    loadProjects();
    loadRecentSearches();
    initVoiceRecognition();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await getProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentSearches = () => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  };

  const saveRecentSearch = (term) => {
    if (!term.trim()) return;
    
    const updated = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  };

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = 'es-ES';
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setSearchTerm(transcript);
        saveRecentSearch(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  };

  const startVoiceSearch = () => {
    if (recognitionRef.current) {
      setIsListening(true);
      recognitionRef.current.start();
    } else {
      alert('Tu navegador no soporta búsqueda por voz');
    }
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

  // Filtrar proyectos
  const filteredProjects = projects
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
        p.description.toLowerCase().includes(search) ||
        p.responsible.toLowerCase().includes(search) ||
        p.year.includes(search) ||
        p.company.toLowerCase().includes(search)
      );
    });

  // Sugerencias (primeros 5 resultados)
  const suggestions = filteredProjects.slice(0, 5);

  // Click fuera cierra sugerencias
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bebas tracking-wider mb-2">MIS PROYECTOS</h1>
              <p className="text-zinc-400">Gestión de producciones activas</p>
            </div>
            
            <button
              onClick={() => navigate('/projects/create')}
              className="flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
            >
              <Plus size={18} />
              NUEVO PROYECTO
            </button>
          </div>

          {/* Búsqueda y Filtros */}
          <div className="flex items-center gap-4">
            {/* Filtros */}
            <div className="flex gap-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-4 py-2 text-sm font-semibold rounded-sm transition-colors ${
                  statusFilter === 'all'
                    ? 'bg-amber-500 text-zinc-950'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }`}
              >
                TODOS ({projects.length})
              </button>
              <button
                onClick={() => setStatusFilter('en_curso')}
                className={`px-4 py-2 text-sm font-semibold rounded-sm transition-colors ${
                  statusFilter === 'en_curso'
                    ? 'bg-amber-500 text-zinc-950'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }`}
              >
                EN CURSO ({projects.filter(p => p.status === 'en_curso').length})
              </button>
              <button
                onClick={() => setStatusFilter('cerrado')}
                className={`px-4 py-2 text-sm font-semibold rounded-sm transition-colors ${
                  statusFilter === 'cerrado'
                    ? 'bg-amber-500 text-zinc-950'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }`}
              >
                CERRADOS ({projects.filter(p => p.status === 'cerrado').length})
              </button>
            </div>

            {/* BÚSQUEDA CON TODAS LAS CARACTERÍSTICAS */}
            <div className="flex-1 relative" ref={searchRef}>
              <div className="relative">
                <Search className="absolute left-4 top-3.5 text-zinc-500" size={20} />
                <input
                  type="search"
                  placeholder="🔍 Buscar por OC, nombre, año, responsable..."
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onFocus={() => searchTerm && setShowSuggestions(true)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
                  className="w-full px-4 py-3 pl-12 pr-24 bg-zinc-900 border border-zinc-700 rounded-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-amber-500 transition-colors"
                />
                
                {/* Botones: Limpiar + Micrófono */}
                <div className="absolute right-2 top-2 flex items-center gap-1">
                  {searchTerm && (
                    <button
                      onClick={clearSearch}
                      className="p-1.5 hover:bg-zinc-800 rounded-sm transition-colors"
                      title="Limpiar búsqueda"
                    >
                      <X size={18} className="text-zinc-500" />
                    </button>
                  )}
                  
                  <button
                    onClick={startVoiceSearch}
                    disabled={isListening}
                    className={`p-1.5 rounded-sm transition-colors ${
                      isListening 
                        ? 'bg-red-500 text-white animate-pulse' 
                        : 'hover:bg-zinc-800 text-zinc-500'
                    }`}
                    title="Búsqueda por voz"
                  >
                    <Mic size={18} />
                  </button>
                </div>
              </div>

              {/* DROPDOWN: Sugerencias + Historial */}
              {showSuggestions && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-96 overflow-y-auto z-50">
                  {/* Sugerencias de proyectos */}
                  {searchTerm && suggestions.length > 0 && (
                    <div>
                      <div className="px-4 py-2 text-xs text-zinc-500 font-mono border-b border-zinc-800">
                        PROYECTOS ENCONTRADOS
                      </div>
                      {suggestions.map((project) => (
                        <div
                          key={project.id}
                          onClick={() => {
                            navigate(`/projects/${project.id}`);
                            saveRecentSearch(searchTerm);
                          }}
                          className="px-4 py-3 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0"
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
                              <p className="text-amber-500 font-bold">{project.total_amount?.toFixed(2)}€</p>
                              <p className="text-xs text-zinc-500">{project.tickets_count} tickets</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Sin resultados */}
                  {searchTerm && suggestions.length === 0 && (
                    <div className="px-4 py-8 text-center text-zinc-500">
                      <p className="text-sm">No se encontraron proyectos</p>
                    </div>
                  )}

                  {/* Historial de búsquedas recientes */}
                  {!searchTerm && recentSearches.length > 0 && (
                    <div>
                      <div className="px-4 py-2 text-xs text-zinc-500 font-mono border-b border-zinc-800 flex items-center gap-2">
                        <Clock size={14} />
                        BÚSQUEDAS RECIENTES
                      </div>
                      {recentSearches.map((term, index) => (
                        <div
                          key={index}
                          onClick={() => {
                            setSearchTerm(term);
                            setShowSuggestions(true);
                          }}
                          className="px-4 py-2.5 hover:bg-zinc-800 cursor-pointer transition-colors border-b border-zinc-800/50 last:border-0 flex items-center gap-2"
                        >
                          <Search size={14} className="text-zinc-600" />
                          <span className="text-sm text-zinc-300">{term}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Contador resultados */}
          <p className="text-sm text-zinc-500 mt-4">
            Mostrando {filteredProjects.length} de {projects.length} proyectos
            {searchTerm && ` para "${searchTerm}"`}
          </p>
        </div>
      </div>

      {/* Projects Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {filteredProjects.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-12 text-center">
            <p className="text-zinc-400 mb-2">No hay proyectos que mostrar</p>
            {searchTerm && (
              <button
                onClick={clearSearch}
                className="text-amber-500 hover:text-amber-400 text-sm"
              >
                Limpiar búsqueda
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-6 cursor-pointer transition-all hover:shadow-lg hover:shadow-amber-500/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bebas tracking-wider mb-1">{project.creative_code}</h3>
                    <span className={`inline-block px-2 py-1 text-xs font-mono rounded-sm border ${
                      project.status === 'en_curso'
                        ? 'bg-green-500/20 text-green-400 border-green-500/30'
                        : 'bg-gray-100 text-gray-800 border-gray-300'
                    }`}>
                      {project.status === 'en_curso' ? 'EN CURSO' : 'CERRADO'}
                    </span>
                  </div>
                </div>

                <p className="text-sm text-zinc-300 mb-4 line-clamp-2">{project.description}</p>

                <div className="space-y-2 mb-4 text-sm text-zinc-500">
                  <div className="flex items-center gap-2">
                    <span>👤</span>
                    <span>{project.responsible}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>📅</span>
                    <span>{project.year}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🎫</span>
                    <span>{project.tickets_count} tickets</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">IMPORTE TOTAL</p>
                  <p className="text-2xl font-bold text-amber-500">{project.total_amount?.toFixed(2)}€</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
