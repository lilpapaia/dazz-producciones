import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Globe, Building2, BarChart3, ChevronDown, ChevronRight, Download } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getCompleteStatistics } from '../services/api';

const Statistics = () => {
  const currentYear = new Date().getFullYear();
  
  // State
  const [year, setYear] = useState(currentYear);
  const [quarter, setQuarter] = useState('');
  const [geoFilter, setGeoFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [expandedCountries, setExpandedCountries] = useState(new Set());

  // Load data
  useEffect(() => {
    loadStatistics();
  }, [year, quarter, geoFilter]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      // Convertir valores vacíos a null explícitamente
      const quarterNum = quarter && quarter !== '' ? parseInt(quarter) : null;
      const geoFilterValue = geoFilter && geoFilter !== '' ? geoFilter : null;
      
      // Debug - ver qué se está enviando
      console.log('📊 Cargando estadísticas con filtros:', { 
        year, 
        quarter: quarterNum, 
        geoFilter: geoFilterValue 
      });
      
      const response = await getCompleteStatistics(year, quarterNum, geoFilterValue);
      setData(response.data);
      
      // Debug - ver qué se recibió
      console.log('✅ Datos recibidos:', {
        total_spent: response.data.overview.total_spent,
        international_spent: response.data.overview.international_spent,
        iva_reclamable: response.data.overview.iva_reclamable,
        paises: response.data.foreign_breakdown.length
      });
    } catch (error) {
      console.error('❌ Error cargando estadísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCountry = (countryCode) => {
    const newExpanded = new Set(expandedCountries);
    if (newExpanded.has(countryCode)) {
      newExpanded.delete(countryCode);
    } else {
      newExpanded.add(countryCode);
    }
    setExpandedCountries(newExpanded);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
          <p className="text-zinc-400">Cargando estadísticas...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <p className="text-zinc-400">No hay datos disponibles</p>
      </div>
    );
  }

  const { overview, monthly_evolution, currency_distribution, foreign_breakdown } = data;

  // Colores para gráficos
  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <h1 className="text-4xl font-bebas tracking-wider mb-2">ESTADÍSTICAS</h1>
          <p className="text-zinc-400 text-sm">Análisis de gastos nacionales e internacionales</p>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        
        {/* Info Box */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-sm p-4">
          <h3 className="text-blue-400 font-semibold text-sm mb-2">ℹ️ Clasificación Geográfica</h3>
          <p className="text-zinc-400 text-sm">
            <strong className="text-zinc-300">Nacional:</strong> España peninsular + Baleares • 
            <strong className="text-zinc-300 ml-2">UE:</strong> Canarias + Resto Unión Europea • 
            <strong className="text-zinc-300 ml-2">Internacional:</strong> Resto del mundo (USD, GBP, CHF, etc.)
          </p>
        </div>

        {/* Filtros */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Año */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Año
              </label>
              <select
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
              >
                <option value={currentYear}>{currentYear}</option>
                <option value={currentYear - 1}>{currentYear - 1}</option>
                <option value={currentYear - 2}>{currentYear - 2}</option>
              </select>
            </div>

            {/* Trimestre */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Trimestre
              </label>
              <select
                value={quarter}
                onChange={(e) => setQuarter(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
              >
                <option value="">Año completo</option>
                <option value="1">Q1 (Ene-Mar)</option>
                <option value="2">Q2 (Abr-Jun)</option>
                <option value="3">Q3 (Jul-Sep)</option>
                <option value="4">Q4 (Oct-Dic)</option>
              </select>
            </div>

            {/* Tipo gastos */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Tipo gastos
              </label>
              <select
                value={geoFilter}
                onChange={(e) => setGeoFilter(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
              >
                <option value="">Todos</option>
                <option value="NACIONAL">Solo nacionales (ESP)</option>
                <option value="UE">Solo UE (EUR)</option>
                <option value="INTERNACIONAL">Solo internacionales</option>
              </select>
            </div>
          </div>
        </div>

        {/* Cards principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total gastado */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <DollarSign size={32} className="text-amber-500" />
              <TrendingUp size={20} className="text-green-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Total Gastado {year}
            </p>
            <p className="text-3xl font-bold text-amber-500 mb-1">
              {overview.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">Nacional + Internacional</p>
          </div>

          {/* Gastos internacionales */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Globe size={32} className="text-blue-400" />
              <TrendingUp size={20} className="text-green-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Gastos Internacionales
            </p>
            <p className="text-3xl font-bold text-blue-400 mb-1">
              {overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">UE + Resto mundo</p>
          </div>

          {/* IVA reclamable */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Building2 size={32} className="text-green-400" />
              <div className="bg-green-500/20 px-2 py-1 rounded text-xs font-bold text-green-400">
                RECLAMABLE
              </div>
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              IVA Reclamable
            </p>
            <p className="text-3xl font-bold text-green-400 mb-1">
              {overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">Internacional recuperable</p>
          </div>

          {/* Proyectos */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 size={32} className="text-purple-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Proyectos
            </p>
            <p className="text-3xl font-bold text-purple-400 mb-1">
              {overview.projects_total}
            </p>
            <p className="text-xs text-zinc-400">
              {overview.projects_closed} cerrados, {overview.projects_open} en curso
            </p>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Evolución mensual */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <TrendingUp size={20} className="text-amber-500" />
              Evolución Gastos Mensual
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthly_evolution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                <XAxis 
                  dataKey="month_name" 
                  stroke="#71717a"
                  tick={{ fill: '#a1a1aa', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#71717a"
                  tick={{ fill: '#a1a1aa', fontSize: 12 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#18181b', 
                    border: '1px solid #3f3f46',
                    borderRadius: '4px',
                    color: '#f4f4f5'
                  }}
                  formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 'Total']}
                />
                <Line 
                  type="monotone" 
                  dataKey="total" 
                  stroke="#f59e0b" 
                  strokeWidth={3}
                  dot={{ fill: '#f59e0b', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Distribución por origen */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Globe size={20} className="text-amber-500" />
              Distribución por Origen
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={currency_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ label, percentage }) => `${label} (${percentage}%)`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="total"
                >
                  {currency_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#18181b', 
                    border: '1px solid #3f3f46',
                    borderRadius: '4px',
                    color: '#f4f4f5'
                  }}
                  formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 'Total']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sección Gastos Internacionales */}
        {foreign_breakdown.length > 0 && (
          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-2 border-blue-500/30 rounded-sm p-8">
            
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Globe size={28} className="text-blue-400" />
                <h2 className="text-2xl font-bold text-blue-400">GASTOS INTERNACIONALES</h2>
                <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">
                  IVA RECLAMABLE
                </span>
              </div>
            </div>

            {/* Mini stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-zinc-900 border border-blue-500/30 rounded-sm p-4">
                <p className="text-xs text-blue-300 font-semibold uppercase mb-1">Total Internacional</p>
                <p className="text-2xl font-bold text-blue-400">
                  {overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                </p>
              </div>
              <div className="bg-zinc-900 border border-green-500/30 rounded-sm p-4">
                <p className="text-xs text-green-300 font-semibold uppercase mb-1">IVA Reclamable</p>
                <p className="text-2xl font-bold text-green-400">
                  {overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                </p>
              </div>
              <div className="bg-zinc-900 border border-purple-500/30 rounded-sm p-4">
                <p className="text-xs text-purple-300 font-semibold uppercase mb-1">Proyectos Afectados</p>
                <p className="text-2xl font-bold text-purple-400">
                  {foreign_breakdown.reduce((sum, country) => sum + country.projects_count, 0)}
                </p>
              </div>
              <div className="bg-zinc-900 border border-amber-500/30 rounded-sm p-4">
                <p className="text-xs text-amber-300 font-semibold uppercase mb-1">Países/Regiones</p>
                <p className="text-2xl font-bold text-amber-400">
                  {foreign_breakdown.length}
                </p>
              </div>
            </div>

            {/* Tabla expandible */}
            <div className="bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">
              
              {/* Header tabla */}
              <div className="bg-zinc-800 px-6 py-4 flex items-center justify-between border-b border-zinc-700">
                <h3 className="font-semibold">Desglose por País/Divisa (Click para ver proyectos)</h3>
                <button className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-2 rounded-sm text-sm font-bold transition-colors">
                  <Download size={16} />
                  Exportar Informe IVA
                </button>
              </div>

              {/* Tabla */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-zinc-800/50">
                    <tr className="border-b border-zinc-700">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        País/Región
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        Divisa
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        Total Gastado
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        IVA Reclamable (EUR)
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        Proyectos
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {foreign_breakdown.map((country) => {
                      const isExpanded = expandedCountries.has(country.country_code);
                      
                      return (
                        <>
                          {/* Fila país */}
                          <tr
                            key={country.country_code}
                            onClick={() => toggleCountry(country.country_code)}
                            className="border-b border-zinc-800 hover:bg-zinc-800/50 cursor-pointer transition-colors"
                          >
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                {isExpanded ? (
                                  <ChevronDown size={18} className="text-amber-500" />
                                ) : (
                                  <ChevronRight size={18} className="text-zinc-600" />
                                )}
                                <span className="font-medium">{country.country_name}</span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  country.geo_classification === 'UE' 
                                    ? 'bg-blue-500/20 text-blue-400' 
                                    : 'bg-purple-500/20 text-purple-400'
                                }`}>
                                  {country.geo_classification}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs font-semibold">
                                {country.currency}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right font-semibold">
                              {country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                            </td>
                            <td className="px-6 py-4 text-right">
                              <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-sm font-bold">
                                {country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                              </span>
                            </td>
                            <td className="px-6 py-4 text-center font-semibold">
                              {country.projects_count}
                            </td>
                          </tr>

                          {/* Fila expandida con proyectos */}
                          {isExpanded && (
                            <tr className="bg-zinc-950">
                              <td colSpan="5" className="px-12 py-6">
                                <div className="space-y-3">
                                  <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-3">
                                    Proyectos con gastos en {country.country_name} ({country.currency}):
                                  </p>
                                  {country.projects.map((project) => (
                                    <div
                                      key={project.id}
                                      className="bg-zinc-900 border border-zinc-800 rounded-sm p-4 hover:border-amber-500 transition-colors flex items-center justify-between"
                                    >
                                      <div>
                                        <p className="font-semibold text-sm text-zinc-100 mb-1">
                                          {project.description}
                                        </p>
                                        <p className="text-xs text-zinc-500 font-mono">
                                          {project.creative_code}
                                        </p>
                                      </div>
                                      <div className="text-right">
                                        <p className="font-bold text-amber-500">
                                          {project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                        </p>
                                        {project.foreign_amount && (
                                          <p className="text-xs text-zinc-500">
                                            ({project.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {project.currency})
                                          </p>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Statistics;
