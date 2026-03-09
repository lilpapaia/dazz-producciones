import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, DollarSign, Globe, Building2, BarChart3, ChevronDown, ChevronRight, Download, FileText } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getCompleteStatistics, getAvailableYears, getCompanies } from '../services/api';
import { useAuth } from '../context/AuthContext';
import jsPDF from 'jspdf';

const Statistics = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const currentYear = new Date().getFullYear();
  
  // State
  const [year, setYear] = useState(currentYear);
  const [quarter, setQuarter] = useState('');
  const [geoFilter, setGeoFilter] = useState('');
  const [companyId, setCompanyId] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [expandedCountries, setExpandedCountries] = useState(new Set());
  const [expandedProjects, setExpandedProjects] = useState(new Set());
  const [expandedCompanies, setExpandedCompanies] = useState(new Set());
  const [availableYears, setAvailableYears] = useState([currentYear]);

  // Load available years on mount
  useEffect(() => {
    const loadYears = async () => {
      try {
        const response = await getAvailableYears();
        if (response.data && response.data.length > 0) {
          setAvailableYears(response.data);
          // Si el año actual no está en la lista, usar el más reciente
          if (!response.data.includes(currentYear)) {
            setYear(response.data[0]);
          }
        }
      } catch (error) {
        console.error('Error loading available years:', error);
      }
    };
    loadYears();
  }, []);

  // Load companies on mount
  useEffect(() => {
    const loadCompanies = async () => {
      try {
        const response = await getCompanies();
        setCompanies(response.data);
        
        // Si es BOSS, auto-seleccionar su empresa
        if (user?.role === 'BOSS') {
          const userCompanyIds = user.companies?.map(c => c.id) || [];
          if (userCompanyIds.length > 0) {
            setCompanyId(userCompanyIds[0]);
          }
        }
      } catch (error) {
        console.error('Error loading companies:', error);
      }
    };
    loadCompanies();
  }, [user]);

  // Load data
  useEffect(() => {
    loadStatistics();
  }, [year, quarter, geoFilter, companyId]);

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
        geoFilter: geoFilterValue,
        companyId
      });
      
      const response = await getCompleteStatistics(year, quarterNum, geoFilterValue, companyId);
      setData(response.data);
      
      // Debug - ver qué se recibió
      console.log('✅ Datos recibidos:', response.data);
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

  const toggleProject = (projectId) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
    }
    setExpandedProjects(newExpanded);
  };

  const toggleCompany = (companyId) => {
    const newExpanded = new Set(expandedCompanies);
    if (newExpanded.has(companyId)) {
      newExpanded.delete(companyId);
    } else {
      newExpanded.add(companyId);
    }
    setExpandedCompanies(newExpanded);
  };

  const exportPDFReport = () => {
    if (!data || !data.foreign_breakdown || data.foreign_breakdown.length === 0) {
      alert('No hay datos internacionales para exportar');
      return;
    }

    const doc = new jsPDF();
    const { overview, foreign_breakdown } = data;
    
    // Debug
    console.log('📄 Exportando PDF con:', { overview, foreign_breakdown });
    
    // Helper para obtener símbolo de moneda
    const getCurrencySymbol = (currency) => {
      // Usar símbolos ASCII simples para evitar problemas de encoding
      return ''; // No usar símbolos, solo el código de moneda
    };

    // Colores
    const colors = {
      primary: [245, 158, 11], // amber-500
      secondary: [59, 130, 246], // blue-500
      success: [34, 197, 94], // green-500
      gray: [161, 161, 170], // zinc-400
      darkGray: [82, 82, 91], // zinc-600
    };

    let yPos = 20;
    const lineHeight = 6;
    const pageHeight = doc.internal.pageSize.height;
    const pageWidth = doc.internal.pageSize.width;

    // Función para verificar si necesitamos nueva página
    const checkPageBreak = (requiredSpace) => {
      if (yPos + requiredSpace > pageHeight - 20) {
        doc.addPage();
        yPos = 20;
        return true;
      }
      return false;
    };

    // Función para dibujar caja con fondo
    const drawBox = (x, y, w, h, fillColor) => {
      doc.setFillColor(...fillColor);
      doc.rect(x, y, w, h, 'F');
    };

    // =============== HEADER CON FONDO ===============
    drawBox(0, 0, pageWidth, 45, [24, 24, 27]); // zinc-900
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont(undefined, 'bold');
    doc.text('INFORME IVA RECLAMABLE', pageWidth / 2, 20, { align: 'center' });
    
    doc.setFontSize(14);
    doc.setFont(undefined, 'normal');
    doc.text(`Año ${year}${quarter ? ` - Q${quarter}` : ''}`, pageWidth / 2, 30, { align: 'center' });
    
    // Fecha generación
    doc.setFontSize(9);
    doc.setTextColor(...colors.gray);
    doc.text(`Generado: ${new Date().toLocaleDateString('es-ES')}`, pageWidth / 2, 38, { align: 'center' });
    
    yPos = 55;
    doc.setTextColor(0, 0, 0);

    // =============== RESUMEN CON CAJA ===============
    checkPageBreak(45);
    
    // Caja fondo
    drawBox(15, yPos - 5, pageWidth - 30, 40, [254, 243, 199]); // amber-100
    
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.setTextColor(...colors.primary);
    doc.text('RESUMEN', 20, yPos + 3);
    yPos += 10;
    
    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    doc.setTextColor(0, 0, 0);
    
    const resumeItems = [
      `Total Internacional: ${overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
      `IVA Reclamable: ${overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
      `Países: ${foreign_breakdown.length}  |  Proyectos: ${foreign_breakdown.reduce((sum, c) => sum + c.projects_count, 0)}`
    ];
    
    resumeItems.forEach(item => {
      doc.text(item, 25, yPos);
      yPos += lineHeight + 1;
    });
    
    yPos += 15;

    // =============== DESGLOSE POR PAÍS ===============
    foreign_breakdown.forEach((country, countryIndex) => {
      checkPageBreak(60);

      // Caja país
      drawBox(15, yPos - 5, pageWidth - 30, 12, [219, 234, 254]); // blue-100
      
      doc.setFontSize(13);
      doc.setFont(undefined, 'bold');
      doc.setTextColor(...colors.secondary);
      doc.text(`${country.country_name} (${country.currency})`, 20, yPos + 2);
      yPos += 12;

      doc.setFontSize(9);
      doc.setFont(undefined, 'normal');
      doc.setTextColor(...colors.darkGray);
      doc.text(`Clasificación: ${country.geo_classification}  |  Total: ${country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€  |  IVA Reclamable: ${country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 20, yPos);
      yPos += 10;
      doc.setTextColor(0, 0, 0);

      // PROYECTOS
      country.projects.forEach((project, projIndex) => {
        checkPageBreak(40);

        // Línea separadora
        doc.setDrawColor(...colors.gray);
        doc.setLineWidth(0.3);
        doc.line(20, yPos, pageWidth - 20, yPos);
        yPos += 6;

        doc.setFontSize(11);
        doc.setFont(undefined, 'bold');
        doc.text(`PROYECTO: ${project.creative_code} - ${project.description}`, 20, yPos);
        yPos += 7;

        doc.setFontSize(9);
        doc.setFont(undefined, 'normal');
        doc.text(`Total Proyecto: ${project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 25, yPos);
        yPos += 8;

        // TICKETS - Ya vienen filtrados por is_foreign=true del backend
        const internationalTickets = project.tickets || [];
        
        console.log(`📋 Proyecto ${project.creative_code}: ${internationalTickets.length} tickets internacionales`);
        
        if (internationalTickets.length > 0) {
          doc.setFont(undefined, 'bold');
          doc.setTextColor(...colors.success);
          doc.text(`> TICKETS INTERNACIONALES (${internationalTickets.length}):`, 25, yPos);
          yPos += 7;
          doc.setTextColor(0, 0, 0);

          internationalTickets.forEach((ticket, index) => {
            checkPageBreak(30);

            const currSymbol = getCurrencySymbol(ticket.currency);

            // Caja ticket
            drawBox(28, yPos - 3, pageWidth - 56, 25, [249, 250, 251]); // gray-50
            
            doc.setFontSize(9);
            doc.setFont(undefined, 'bold');
            doc.text(`${index + 1}. ${ticket.provider}`, 32, yPos + 2);
            yPos += 6;

            doc.setFont(undefined, 'normal');
            doc.setFontSize(8);
            
            const ticketInfo = [
              `  Fecha: ${ticket.date || 'N/A'}`,
              `  Archivo: ${(ticket.file_name || 'N/A').substring(0, 35)}${(ticket.file_name?.length > 35) ? '...' : ''}`,
              `  Total: ${(ticket.foreign_amount || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })} ${ticket.currency}`,
              `  Tax: ${(ticket.foreign_tax_amount || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })} ${ticket.currency}`,
            ];
            
            ticketInfo.forEach(info => {
              doc.text(info, 35, yPos);
              yPos += 5;
            });
            
            // IVA reclamable destacado
            doc.setFont(undefined, 'bold');
            doc.setTextColor(...colors.success);
            doc.text(`> IVA Reclamable: ${(ticket.foreign_tax_eur || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 35, yPos);
            yPos += 8;
            doc.setTextColor(0, 0, 0);
          });
        } else {
          doc.setFontSize(8);
          doc.setTextColor(...colors.gray);
          doc.text(`(No hay tickets internacionales en este proyecto)`, 25, yPos);
          yPos += 6;
          doc.setTextColor(0, 0, 0);
        }

        yPos += 5;
      });

      yPos += 8;
    });

    // =============== FOOTER EN TODAS LAS PÁGINAS ===============
    const totalPages = doc.internal.getNumberOfPages();
    
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      
      // Línea superior footer
      doc.setDrawColor(...colors.gray);
      doc.setLineWidth(0.5);
      doc.line(20, pageHeight - 15, pageWidth - 20, pageHeight - 15);
      
      // Texto footer
      doc.setFontSize(8);
      doc.setFont(undefined, 'italic');
      doc.setTextColor(...colors.darkGray);
      doc.text(`Página ${i} de ${totalPages}`, pageWidth / 2, pageHeight - 8, { align: 'center' });
    }

    // =============== GUARDAR PDF ===============
    const fileName = `Informe_IVA_${year}${quarter ? `_Q${quarter}` : ''}_${new Date().getTime()}.pdf`;
    doc.save(fileName);
    
    console.log('✅ PDF generado:', fileName);
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
          <div className={`grid grid-cols-1 ${user?.role === 'ADMIN' ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-4`}>
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
                {availableYears.map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
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

            {/* Empresa - Solo para ADMIN */}
            {user?.role === 'ADMIN' && (
              <div>
                <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                  Empresa
                </label>
                <select
                  value={companyId || ''}
                  onChange={(e) => setCompanyId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
                >
                  <option value="">TODAS LAS EMPRESAS</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name} {c.cif && `(${c.cif})`}
                    </option>
                  ))}
                </select>
              </div>
            )}
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

        {/* Cards por empresa - Solo ADMIN en modo TODAS */}
        {user?.role === 'ADMIN' && !companyId && data?.companies && data.companies.length > 0 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h2 className="text-2xl font-bebas tracking-wider mb-6 flex items-center gap-2">
              <Building2 size={24} className="text-amber-500" />
              RESUMEN POR EMPRESA
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              {data.companies.map(company => (
                <div key={company.company_id} className="bg-zinc-950 border border-zinc-700 rounded-sm p-6 hover:border-amber-500 transition-colors">
                  <div className="flex items-center gap-2 mb-3">
                    <Building2 size={20} className="text-amber-500" />
                    <h3 className="font-bold text-zinc-100">{company.company_name}</h3>
                  </div>
                  {company.cif && (
                    <p className="text-xs text-zinc-500 font-mono mb-3">CIF: {company.cif}</p>
                  )}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-zinc-400">Total gastado:</span>
                      <span className="text-lg font-bold text-amber-500">
                        {company.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-zinc-400">IVA reclamable:</span>
                      <span className="text-md font-semibold text-green-400">
                        {company.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-zinc-800">
                      <span className="text-xs text-zinc-500">Proyectos:</span>
                      <span className="text-sm text-zinc-300">{company.projects_count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Total global */}
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-sm p-6">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-zinc-400 mb-1">TOTAL GLOBAL</p>
                  <p className="text-3xl font-bold text-amber-500">
                    {data.overview.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                  </p>
                </div>
                <div className="text-left md:text-right">
                  <p className="text-sm text-zinc-400 mb-1">IVA TOTAL RECLAMABLE</p>
                  <p className="text-2xl font-bold text-green-400">
                    {data.overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
         {/* Evolución mensual */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <TrendingUp size={20} className="text-amber-500" />
              Evolución Gastos Mensual
            </h3>
            
            {monthly_evolution && monthly_evolution.length > 0 && monthly_evolution.some(m => m.total > 0) ? (
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
            ) : (
              <div className="h-[300px] flex items-center justify-center">
                <div className="text-center">
                  <p className="text-zinc-500 text-lg mb-2">📊</p>
                  <p className="text-zinc-500">No hay datos de gastos{quarter ? ` en el Q${quarter}` : ''} de {year}</p>
                  <p className="text-zinc-600 text-sm mt-1">
                    {companyId ? 'para esta empresa' : 'en el período seleccionado'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Distribución por origen */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Globe size={20} className="text-amber-500" />
              Distribución por Origen
            </h3>
            
            {currency_distribution && currency_distribution.length > 0 ? (
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
                      <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
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
            ) : (
              <div className="h-[300px] flex items-center justify-center">
                <div className="text-center">
                  <p className="text-zinc-500 text-lg mb-2">🌍</p>
                  <p className="text-zinc-500">No hay gastos registrados{quarter ? ` en el Q${quarter}` : ''} de {year}</p>
                  <p className="text-zinc-600 text-sm mt-1">
                    {companyId ? 'para esta empresa' : 'en el período seleccionado'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sección Gastos Internacionales */}
        {foreign_breakdown.length > 0 && (
          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-2 border-blue-500/30 rounded-sm p-4 sm:p-8">
            
            {/* Header - Responsive */}
            <div className="mb-6">
              {/* Móvil: Centrado y compacto */}
              <div className="flex flex-col items-center text-center sm:hidden gap-3">
                <h2 className="text-lg font-bold text-blue-400">GASTOS INTERNACIONALES</h2>
                <div className="flex items-center gap-2 flex-wrap justify-center">
                  <span className="bg-amber-500 text-zinc-950 text-xs font-bold px-3 py-1 rounded">
                    IVA RECLAMABLE
                  </span>
                  <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">
                    {year}
                  </span>
                  {quarter && quarter !== '' && (
                    <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">
                      Q{quarter}
                    </span>
                  )}
                </div>
              </div>
              
              {/* Desktop: Layout con badges */}
              <div className="hidden sm:block">
                <h2 className="text-2xl font-bold text-blue-400 mb-3">GASTOS INTERNACIONALES</h2>
                <div className="flex items-center gap-2">
                  <span className="bg-amber-500 text-zinc-950 text-xs font-bold px-3 py-1 rounded">
                    IVA RECLAMABLE
                  </span>
                  <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">
                    {year}
                  </span>
                  {quarter && quarter !== '' && (
                    <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">
                      Q{quarter}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Mini stats - 2x2 en móvil, 4 en fila en desktop */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
              <div className="bg-zinc-900 border border-blue-500/30 rounded-sm p-3 sm:p-4">
                <p className="text-xs text-blue-300 font-semibold uppercase mb-1">Total Internacional</p>
                <p className="text-xl sm:text-2xl font-bold text-blue-400">
                  {overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                </p>
              </div>
              <div className="bg-zinc-900 border border-green-500/30 rounded-sm p-3 sm:p-4">
                <p className="text-xs text-green-300 font-semibold uppercase mb-1">IVA Reclamable</p>
                <p className="text-xl sm:text-2xl font-bold text-green-400">
                  {overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                </p>
              </div>
              <div className="bg-zinc-900 border border-purple-500/30 rounded-sm p-3 sm:p-4">
                <p className="text-xs text-purple-300 font-semibold uppercase mb-1">Proyectos</p>
                <p className="text-xl sm:text-2xl font-bold text-purple-400">
                  {foreign_breakdown.reduce((sum, country) => sum + country.projects_count, 0)}
                </p>
              </div>
              <div className="bg-zinc-900 border border-amber-500/30 rounded-sm p-3 sm:p-4">
                <p className="text-xs text-amber-300 font-semibold uppercase mb-1">Países</p>
                <p className="text-xl sm:text-2xl font-bold text-amber-400">
                  {foreign_breakdown.length}
                </p>
              </div>
            </div>

            {/* Botón Exportar - Solo en móvil, debajo de las stats */}
            <div className="sm:hidden mb-6">
              <button 
                onClick={exportPDFReport}
                className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-3 rounded-sm text-sm font-bold transition-colors"
              >
                <Download size={16} />
                Exportar Informe IVA
              </button>
            </div>

            {/* Vista MÓVIL: Chips horizontales */}
            <div className="sm:hidden space-y-4">
              {foreign_breakdown.map((country) => {
                const isExpanded = expandedCountries.has(country.country_code);
                
                return (
                  <div key={country.country_code} className="bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">
                    {/* Chip del país - clickeable */}
                    <div
                      onClick={() => toggleCountry(country.country_code)}
                      className="p-4 cursor-pointer active:bg-zinc-800 transition-colors"
                    >
                      {/* Línea 1: Chevron + Nombre del país */}
                      <div className="flex items-center gap-2 mb-2">
                        {isExpanded ? (
                          <ChevronDown size={18} className="text-amber-500" />
                        ) : (
                          <ChevronRight size={18} className="text-zinc-600" />
                        )}
                        <span className="font-semibold text-lg">{country.country_name}</span>
                      </div>

                      {/* Línea 2: Badges (Clasificación + Divisa) */}
                      <div className="flex items-center gap-2 mb-3 ml-6">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          country.geo_classification === 'UE' 
                            ? 'bg-blue-500/20 text-blue-400' 
                            : 'bg-purple-500/20 text-purple-400'
                        }`}>
                          {country.geo_classification}
                        </span>
                        <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs font-semibold">
                          {country.currency}
                        </span>
                      </div>
                      
                      {/* Línea 3: Info resumida */}
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <p className="text-zinc-500 text-xs">Total</p>
                          <p className="font-semibold">{country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€</p>
                        </div>
                        <div className="text-right">
                          <p className="text-zinc-500 text-xs">IVA Reclamable</p>
                          <p className="text-green-400 font-bold">{country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€</p>
                        </div>
                        <div className="text-right">
                          <p className="text-zinc-500 text-xs">Proyectos</p>
                          <p className="font-semibold">{country.projects_count}</p>
                        </div>
                      </div>
                    </div>

                    {/* Contenido expandido - Proyectos */}
                    {isExpanded && (
                      <div className="border-t border-zinc-800 bg-zinc-950 p-4 space-y-3">
                        <p className="text-xs text-zinc-500 font-semibold uppercase">
                          Proyectos ({country.projects_count}):
                        </p>
                        
                        {country.projects.map((project) => {
                          const isProjectExpanded = expandedProjects.has(project.id);
                          
                          return (
                            <div key={project.id} className="space-y-2">
                              {/* Card del proyecto */}
                              <div
                                onClick={() => toggleProject(project.id)}
                                className="bg-zinc-900 border border-zinc-800 rounded-sm p-3 active:bg-zinc-800 transition-colors"
                              >
                                <div className="flex items-start gap-2">
                                  {isProjectExpanded ? (
                                    <ChevronDown size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
                                  ) : (
                                    <ChevronRight size={16} className="text-zinc-600 mt-0.5 flex-shrink-0" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <p className="font-semibold text-sm">{project.description}</p>
                                    <p className="text-xs text-zinc-500 font-mono mt-1">{project.creative_code}</p>
                                    <div className="flex items-center justify-between mt-2">
                                      <span className="text-xs bg-zinc-800 px-2 py-0.5 rounded">
                                        {project.tickets?.length || 0} ticket{project.tickets?.length !== 1 ? 's' : ''}
                                      </span>
                                      <div className="text-right">
                                        <p className="font-bold text-amber-500">{project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€</p>
                                        {project.foreign_amount && (
                                          <p className="text-xs text-zinc-500">
                                            ({project.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {project.currency})
                                          </p>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Tickets del proyecto */}
                              {isProjectExpanded && project.tickets && project.tickets.length > 0 && (
                                <div className="ml-4 space-y-2">
                                  <p className="text-xs text-zinc-600 font-semibold uppercase">
                                    📄 Tickets ({project.tickets.length}):
                                  </p>
                                  {project.tickets.map((ticket) => (
                                    <div
                                      key={ticket.id}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/tickets/${ticket.id}/review?filter=international&project=${project.id}`);
                                      }}
                                      className="bg-zinc-900/50 border border-zinc-800 rounded-sm p-3 active:border-blue-500 transition-colors"
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex-1 min-w-0 pr-2">
                                          <p className="text-sm font-medium truncate">{ticket.provider}</p>
                                          <p className="text-xs text-zinc-500 mt-0.5">
                                            {ticket.date} • {ticket.invoice_number || 'N/A'}
                                          </p>
                                        </div>
                                        <div className="text-right flex-shrink-0">
                                          <p className="text-sm font-bold text-blue-400">
                                            {ticket.final_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                          </p>
                                          {ticket.foreign_amount && (
                                            <p className="text-xs text-zinc-500">
                                              {ticket.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {ticket.currency}
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Vista DESKTOP: Tabla (original) - Oculta en móvil */}
            <div className="hidden sm:block bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">
              
              {/* Header tabla */}
              <div className="bg-zinc-800 px-6 py-4 flex items-center justify-between border-b border-zinc-700">
                <h3 className="font-semibold">Desglose por País/Divisa (Click para ver proyectos)</h3>
                <button 
                  onClick={exportPDFReport}
                  className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-2 rounded-sm text-sm font-bold transition-colors"
                >
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
                                {/* MODO TODAS: Agrupar por empresa */}
                                {user?.role === 'ADMIN' && !companyId && country.companies ? (
                                  <div className="space-y-6">
                                    <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-3">
                                      Proyectos con gastos en {country.country_name}:
                                    </p>
                                    
                                    {/* Agrupar por empresa */}
                                    {country.companies.map((companyGroup) => {
                                      const isCompanyExpanded = expandedCompanies.has(companyGroup.company_id);
                                      
                                      return (
                                        <div key={companyGroup.company_id} className="space-y-3">
                                          {/* Header de empresa - clickeable */}
                                          <div
                                            onClick={() => toggleCompany(companyGroup.company_id)}
                                            className="flex items-center gap-2 text-zinc-300 font-semibold bg-zinc-900/50 px-4 py-3 rounded-sm border border-zinc-800 hover:border-amber-500 cursor-pointer transition-colors"
                                          >
                                            {isCompanyExpanded ? (
                                              <ChevronDown size={18} className="text-amber-500" />
                                            ) : (
                                              <ChevronRight size={18} className="text-zinc-600" />
                                            )}
                                            <Building2 size={16} className="text-amber-500" />
                                            <span>{companyGroup.company_name}</span>
                                            <span className="ml-auto text-xs text-zinc-500">
                                              {companyGroup.projects.length} proyecto{companyGroup.projects.length !== 1 ? 's' : ''}
                                            </span>
                                          </div>
                                          
                                          {/* Proyectos de esta empresa */}
                                          {isCompanyExpanded && companyGroup.projects.map((project) => {
                                            const isProjectExpanded = expandedProjects.has(project.id);
                                            
                                            return (
                                              <div key={project.id} className="ml-6 space-y-2">
                                                {/* Card del proyecto */}
                                                <div
                                                  onClick={() => toggleProject(project.id)}
                                                  className="bg-zinc-900 border border-zinc-800 rounded-sm p-4 hover:border-amber-500 transition-colors cursor-pointer"
                                                >
                                                  <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3 flex-1">
                                                      {isProjectExpanded ? (
                                                        <ChevronDown size={18} className="text-amber-500 flex-shrink-0" />
                                                      ) : (
                                                        <ChevronRight size={18} className="text-zinc-600 flex-shrink-0" />
                                                      )}
                                                      <div>
                                                        <p className="font-semibold text-sm text-zinc-100 mb-1">
                                                          {project.description}
                                                        </p>
                                                        <div className="flex items-center gap-3 text-xs text-zinc-500">
                                                          <span className="font-mono">{project.creative_code}</span>
                                                          <span className="bg-zinc-800 px-2 py-0.5 rounded">
                                                            {project.tickets?.length || 0} ticket{project.tickets?.length !== 1 ? 's' : ''}
                                                          </span>
                                                        </div>
                                                      </div>
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
                                                </div>

                                                {/* Tickets del proyecto */}
                                                {isProjectExpanded && project.tickets && project.tickets.length > 0 && (
                                                  <div className="ml-8 space-y-2 mt-2">
                                                    <p className="text-xs text-zinc-600 font-semibold uppercase mb-2">
                                                      📄 Tickets internacionales:
                                                    </p>
                                                    {project.tickets.map((ticket) => (
                                                      <div
                                                        key={ticket.id}
                                                        onClick={(e) => {
                                                          e.stopPropagation();
                                                          navigate(`/tickets/${ticket.id}/review?filter=international&project=${project.id}`);
                                                        }}
                                                        className="bg-zinc-900/50 border border-zinc-800 rounded-sm p-3 hover:border-blue-500 transition-colors cursor-pointer group"
                                                      >
                                                        <div className="flex items-center justify-between">
                                                          <div className="flex items-center gap-3">
                                                            <FileText size={16} className="text-zinc-600 group-hover:text-blue-400 transition-colors" />
                                                            <div>
                                                              <p className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">
                                                                {ticket.provider}
                                                              </p>
                                                              <div className="flex items-center gap-2 mt-0.5">
                                                                <span className="text-xs text-zinc-600">{ticket.date}</span>
                                                                {ticket.invoice_number && (
                                                                  <>
                                                                    <span className="text-zinc-700">•</span>
                                                                    <span className="text-xs text-zinc-600 font-mono">
                                                                      {ticket.invoice_number}
                                                                    </span>
                                                                  </>
                                                                )}
                                                              </div>
                                                            </div>
                                                          </div>
                                                          <div className="text-right">
                                                            <p className="text-sm font-bold text-zinc-300">
                                                              {ticket.final_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                                            </p>
                                                            {ticket.foreign_amount && (
                                                              <p className="text-xs text-zinc-600">
                                                                {ticket.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {ticket.currency}
                                                              </p>
                                                            )}
                                                            {ticket.foreign_tax_eur && (
                                                              <p className="text-xs text-green-500 font-semibold mt-0.5">
                                                                IVA: {ticket.foreign_tax_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                                              </p>
                                                            )}
                                                          </div>
                                                        </div>
                                                      </div>
                                                    ))}
                                                  </div>
                                                )}
                                              </div>
                                            );
                                          })}
                                        </div>
                                      );
                                    })}
                                  </div>
                                ) : (
                                  /* VISTA NORMAL: Sin agrupar por empresa */
                                  <div className="space-y-3">
                                    <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-3">
                                      Proyectos con gastos en {country.country_name} ({country.currency}):
                                    </p>
                                    {country.projects.map((project) => {
                                      const isProjectExpanded = expandedProjects.has(project.id);
                                      
                                      return (
                                        <div key={project.id} className="space-y-2">
                                          {/* Card del proyecto - ahora expandible */}
                                          <div
                                            onClick={() => toggleProject(project.id)}
                                            className="bg-zinc-900 border border-zinc-800 rounded-sm p-4 hover:border-amber-500 transition-colors cursor-pointer"
                                          >
                                            <div className="flex items-center justify-between">
                                              <div className="flex items-center gap-3 flex-1">
                                                {isProjectExpanded ? (
                                                  <ChevronDown size={18} className="text-amber-500 flex-shrink-0" />
                                                ) : (
                                                  <ChevronRight size={18} className="text-zinc-600 flex-shrink-0" />
                                                )}
                                                <div>
                                                  <p className="font-semibold text-sm text-zinc-100 mb-1">
                                                    {project.description}
                                                  </p>
                                                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                                                    <span className="font-mono">{project.creative_code}</span>
                                                    <span className="bg-zinc-800 px-2 py-0.5 rounded">
                                                      {project.tickets?.length || 0} ticket{project.tickets?.length !== 1 ? 's' : ''}
                                                    </span>
                                                  </div>
                                                </div>
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
                                          </div>

                                          {/* Lista de tickets del proyecto (3er nivel) */}
                                          {isProjectExpanded && project.tickets && project.tickets.length > 0 && (
                                            <div className="ml-8 space-y-2 mt-2">
                                              <p className="text-xs text-zinc-600 font-semibold uppercase mb-2">
                                                📄 Tickets internacionales:
                                              </p>
                                              {project.tickets.map((ticket) => (
                                                <div
                                                  key={ticket.id}
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/tickets/${ticket.id}/review?filter=international&project=${project.id}`);
                                                  }}
                                                  className="bg-zinc-900/50 border border-zinc-800 rounded-sm p-3 hover:border-blue-500 transition-colors cursor-pointer group"
                                                >
                                                  <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                      <FileText size={16} className="text-zinc-600 group-hover:text-blue-400 transition-colors" />
                                                      <div>
                                                        <p className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">
                                                          {ticket.provider}
                                                        </p>
                                                        <div className="flex items-center gap-2 mt-0.5">
                                                          <span className="text-xs text-zinc-600">{ticket.date}</span>
                                                          {ticket.invoice_number && (
                                                            <>
                                                              <span className="text-zinc-700">•</span>
                                                              <span className="text-xs text-zinc-600 font-mono">
                                                                {ticket.invoice_number}
                                                              </span>
                                                            </>
                                                          )}
                                                        </div>
                                                      </div>
                                                    </div>
                                                    <div className="text-right">
                                                      <p className="text-sm font-bold text-zinc-300">
                                                        {ticket.final_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                                      </p>
                                                      {ticket.foreign_amount && (
                                                        <p className="text-xs text-zinc-600">
                                                          {ticket.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {ticket.currency}
                                                        </p>
                                                      )}
                                                      {ticket.foreign_tax_eur && (
                                                        <p className="text-xs text-green-500 font-semibold mt-0.5">
                                                          IVA: {ticket.foreign_tax_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                                                        </p>
                                                      )}
                                                    </div>
                                                  </div>
                                                </div>
                                              ))}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
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
