import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProject, getCompanies } from '../services/api';
import { ArrowLeft, Save, Building2 } from 'lucide-react';
import { showSuccess, showError } from '../utils/toast';
import UserAutocomplete from '../components/UserAutocomplete';

const ProjectCreate = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [emailInput, setEmailInput] = useState('');
  const [clientEmails, setClientEmails] = useState([]);
  const [formData, setFormData] = useState({
    year: new Date().getFullYear().toString(),
    send_date: new Date().toISOString().split('T')[0],
    creative_code: '',
    owner_company_id: '', // ← NUEVO: ID de empresa en lugar de texto
    responsible: '',
    invoice_type: 'PRODUCCION' + new Date().getFullYear(),
    description: '',
    other_invoice_data: '',
    client_oc: '',
    client_data: '',
    client_email: '',
    project_link: ''
  });

  // ← NUEVO: Cargar empresas al montar
  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await getCompanies();
      setCompanies(response.data);
      
      // Si solo hay una empresa, seleccionarla automáticamente
      if (response.data.length === 1) {
        setFormData(prev => ({ ...prev, owner_company_id: response.data[0].id }));
      }
    } catch (error) {
      console.error('Error loading companies:', error);
      showError('Error al cargar empresas. Verifica tus permisos.');
    } finally {
      setLoadingCompanies(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'owner_company_id') {
      // Reset responsable cuando cambia la empresa
      setFormData(prev => ({ ...prev, owner_company_id: value, responsible: '' }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleResponsibleChange = (name) => {
    setFormData({ ...formData, responsible: name });
  };

  const addEmail = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const email = emailInput.trim().replace(/,$/, '');
      if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && !clientEmails.includes(email)) {
        setClientEmails(prev => [...prev, email]);
      }
      setEmailInput('');
    }
  };

  const removeEmail = (email) => {
    setClientEmails(prev => prev.filter(e => e !== email));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Convertir owner_company_id a número
      const dataToSend = {
        ...formData,
        owner_company_id: parseInt(formData.owner_company_id),
        client_email: clientEmails.join(', ')
      };
      
      const response = await createProject(dataToSend);
      showSuccess('Proyecto creado exitosamente');
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      showError('Error al crear proyecto: ' + (error.response?.data?.detail || error.message));
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

            {/* ← NUEVO: Dropdown de empresas */}
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
                EMPRESA FACTURACIÓN *
              </label>
              
              {loadingCompanies ? (
                <div className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-500">
                  Cargando empresas...
                </div>
              ) : companies.length === 0 ? (
                <div className="w-full bg-red-900/20 border border-red-900/30 rounded-sm px-4 py-2.5 text-red-400 text-sm">
                  ⚠️ No tienes empresas asignadas. Contacta con un admin.
                </div>
              ) : (
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
                    <Building2 size={18} />
                  </div>
                  
                  <select
                    name="owner_company_id"
                    value={formData.owner_company_id}
                    onChange={handleChange}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm pl-10 pr-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 appearance-none cursor-pointer"
                    required
                  >
                    <option value="">Selecciona una empresa...</option>
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>
                        {company.name} {company.cif && `(${company.cif})`}
                      </option>
                    ))}
                  </select>
                  
                  {/* Flecha dropdown */}
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              )}
              
              {companies.length > 0 && (
                <p className="text-xs text-zinc-500 mt-1">
                  {companies.length === 1 
                    ? 'Solo tienes acceso a una empresa'
                    : `Tienes acceso a ${companies.length} empresas`
                  }
                </p>
              )}
            </div>
          </div>

          {/* Responsable y Tipo Factura */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* NUEVO: Autocompletado de usuarios */}
            <UserAutocomplete
              value={formData.responsible}
              onChange={handleResponsibleChange}
              companyId={formData.owner_company_id || null}
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

          {/* Email Cliente - múltiples */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL CLIENTE</label>
            <div className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-3 py-2 focus-within:border-amber-500 transition-colors min-h-[42px] flex flex-wrap gap-2 items-center">
              {clientEmails.map(email => (
                <span key={email} className="flex items-center gap-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded px-2 py-0.5 text-xs font-mono">
                  {email}
                  <button type="button" onClick={() => removeEmail(email)} className="text-amber-500 hover:text-red-400 ml-1 leading-none">×</button>
                </span>
              ))}
              <input
                type="email"
                value={emailInput}
                onChange={e => setEmailInput(e.target.value)}
                onKeyDown={addEmail}
                onBlur={() => {
                  if (emailInput.trim() && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.trim())) {
                    setClientEmails(prev => [...prev, emailInput.trim()]);
                    setEmailInput('');
                  }
                }}
                placeholder={clientEmails.length === 0 ? "cliente@empresa.com — pulsa Enter para añadir" : "Añadir otro email..."}
                className="flex-1 min-w-[200px] bg-transparent text-zinc-100 focus:outline-none text-sm py-0.5"
              />
            </div>
            {clientEmails.length > 0 && (
              <p className="text-xs text-zinc-500 mt-1">{clientEmails.length} email{clientEmails.length > 1 ? 's' : ''} añadido{clientEmails.length > 1 ? 's' : ''}</p>
            )}
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
              disabled={loading || !formData.responsible || !formData.owner_company_id || loadingCompanies}
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
