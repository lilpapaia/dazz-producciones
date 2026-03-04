import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects, closeProject } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Plus, FileText, Clock, CheckCircle } from 'lucide-react';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await getProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseProject = async (projectId, e) => {
    e.stopPropagation();
    if (!confirm('¿Cerrar proyecto? Se generará el Excel y se enviará email a Miguel.')) {
      return;
    }

    try {
      await closeProject(projectId);
      alert('✓ Proyecto cerrado exitosamente\n✓ Excel generado\n✓ Email enviado');
      loadProjects();
    } catch (error) {
      alert('Error al cerrar proyecto: ' + (error.response?.data?.detail || error.message));
    }
  };

  const filteredProjects = projects.filter(p => {
    if (filter === 'all') return true;
    return p.status === filter;
  });

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-4xl font-bebas tracking-wider mb-2">MIS PROYECTOS</h2>
            <p className="text-zinc-500 font-mono text-sm">Gestión de producciones activas</p>
          </div>
          <button
            onClick={() => navigate('/projects/new')}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 hover:shadow-amber-500/50 font-bebas text-lg tracking-wider flex items-center gap-2"
          >
            <Plus size={20} /> NUEVO PROYECTO
          </button>
        </div>

        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-sm font-mono text-sm tracking-wider transition-all ${
              filter === 'all'
                ? 'bg-amber-500 text-zinc-950'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            TODOS ({projects.length})
          </button>
          <button
            onClick={() => setFilter('en_curso')}
            className={`px-4 py-2 rounded-sm font-mono text-sm tracking-wider transition-all ${
              filter === 'en_curso'
                ? 'bg-amber-500 text-zinc-950'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            EN CURSO ({projects.filter(p => p.status === 'en_curso').length})
          </button>
          <button
            onClick={() => setFilter('cerrado')}
            className={`px-4 py-2 rounded-sm font-mono text-sm tracking-wider transition-all ${
              filter === 'cerrado'
                ? 'bg-amber-500 text-zinc-950'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            CERRADOS ({projects.filter(p => p.status === 'cerrado').length})
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-12 bg-zinc-900 border border-zinc-800 rounded-sm">
            <FileText size={48} className="mx-auto text-zinc-700 mb-4" />
            <p className="text-zinc-500 text-lg mb-2">No hay proyectos {filter !== 'all' && filter}</p>
            <button
              onClick={() => navigate('/projects/new')}
              className="mt-4 text-amber-500 hover:text-amber-400 font-medium"
            >
              Crear tu primer proyecto
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredProjects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-zinc-900 border border-zinc-800 hover:border-amber-500/50 rounded-sm p-6 cursor-pointer transition-all hover:shadow-lg hover:shadow-amber-500/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-zinc-100">{project.description}</h3>
                      <span className={`px-3 py-1 text-xs font-mono tracking-wider rounded-sm border ${
                        project.status === 'en_curso'
                          ? 'bg-green-500/20 text-green-400 border-green-500/30'
                          : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
                      }`}>
                        {project.status === 'en_curso' ? (
                          <span className="flex items-center gap-1.5">
                            <Clock size={12} /> EN CURSO
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5">
                            <CheckCircle size={12} /> CERRADO
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-500 font-mono">{project.creative_code}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-zinc-800">
                  <div>
                    <p className="text-xs text-zinc-500 font-mono mb-1">RESPONSABLE</p>
                    <p className="text-sm font-semibold text-zinc-300">{project.responsible}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 font-mono mb-1">TICKETS</p>
                    <p className="text-sm font-semibold text-zinc-300">{project.tickets_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 font-mono mb-1">TOTAL</p>
                    <p className="text-lg font-bold text-amber-500">{project.total_amount?.toFixed(2) || '0.00'}€</p>
                  </div>
                </div>

                {project.status === 'en_curso' && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <button
                      onClick={(e) => handleCloseProject(project.id, e)}
                      className="w-full px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 text-sm tracking-wider"
                    >
                      ✓ CERRAR PROYECTO
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
