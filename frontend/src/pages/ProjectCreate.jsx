import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProject } from '../services/api';
import { ArrowLeft, Save } from 'lucide-react';
import UserAutocomplete from '../components/UserAutocomplete';

const ProjectCreate = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    year: new Date().getFullYear().toString(),
    send_date: new Date().toISOString().split('T')[0],
    creative_code: '',
    company: 'DIGITAL ADVERTISING SOCIAL SERVICES SL',
    responsible: '',
    invoice_type: 'PRODUCCION' + new Date().getFullYear(),
    description: '',
    other_invoice_data: '',
    client_oc: '',
    client_data: '',
    client_email: '',
    project_link: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleResponsibleChange = (name) => {
    setFormData({ ...formData, responsible: name });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await createProject(formData);
      alert('✓ Proyecto creado exitosamente');
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      alert('Error al crear proyecto: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver</span>
          </button>
          <h1 className="text-3xl font-bebas tracking-wider">NUEVA PRODUCCIÓN</h1>
          <p className="text-sm text-zinc-500 mt-1">Completa los datos del proyecto</p>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 space-y-6">
          
          {/* Año y Fecha */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">AÑO *</label>
              <input
                type="text"
                name="year"
                value={formData.year}
                onChange={handleChange}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">FECHA ENVÍO FACTURAR *</label>
              <input
                type="date"
                name="send_date"
                value={formData.send_date}
                onChange={handleChange}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 appearance-none [&::-webkit-calendar-picker-indicator]:opacity-100 [&::-webkit-calendar-picker-indicator]:cursor-pointer"
                required
              />
            </div>
          </div>

          {/* Código OC y Empresa */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">CÓDIGO CREATIVO (OC) *</label>
              <input
                type="text"
                name="creative_code"
                value={formData.creative_code}
                onChange={handleChange}
                placeholder="OC-PROD202600XXX"
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMPRESA FACTURACIÓN *</label>
              <input
                type="text"
                name="company"
                value={formData.company}
                onChange={handleChange}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                required
              />
            </div>
          </div>

          {/* Responsable y Tipo Factura */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* NUEVO: Autocompletado de usuarios */}
            <UserAutocomplete
              value={formData.responsible}
              onChange={handleResponsibleChange}
              label="RESPONSABLE"
              required={true}
            />

            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">TIPO FACTURA *</label>
              <input
                type="text"
                name="invoice_type"
                value={formData.invoice_type}
                onChange={handleChange}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                required
              />
            </div>
          </div>

          {/* Descripción/Campaña */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">DESCRIPCIÓN / CAMPAÑA *</label>
            <input
              type="text"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Descripción del proyecto o campaña..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
              required
            />
          </div>

          {/* Otros Datos Factura */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">OTROS DATOS FACTURA</label>
            <input
              type="text"
              name="other_invoice_data"
              value={formData.other_invoice_data}
              onChange={handleChange}
              placeholder="Ej: 3% CARLOS MIMET"
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* OC de Cliente */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">OC DE CLIENTE</label>
            <input
              type="text"
              name="client_oc"
              value={formData.client_oc}
              onChange={handleChange}
              placeholder="Ej: 7000958658"
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Datos Cliente */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">DATOS CLIENTE</label>
            <textarea
              name="client_data"
              value={formData.client_data}
              onChange={handleChange}
              rows={3}
              placeholder="Nombre, dirección, teléfono, CIF..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 resize-none"
            />
          </div>

          {/* Email Cliente */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL CLIENTE</label>
            <input
              type="email"
              name="client_email"
              value={formData.client_email}
              onChange={handleChange}
              placeholder="cliente@empresa.com"
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Link SharePoint */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">LINK PROYECTO SHAREPOINT</label>
            <input
              type="url"
              name="project_link"
              value={formData.project_link}
              onChange={handleChange}
              placeholder="https://dazzledazz.sharepoint.com/..."
              className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Botones */}
          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !formData.responsible}
              className="flex-1 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Save size={18} />
              {loading ? 'CREANDO...' : 'CREAR PROYECTO'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
};

export default ProjectCreate;
