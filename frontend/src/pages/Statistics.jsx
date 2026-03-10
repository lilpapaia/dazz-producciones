import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, DollarSign, Globe, Building2, BarChart3, ChevronDown, ChevronRight, Download, FileText } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getCompleteStatistics, getAvailableYears, getCompanies } from '../services/api';
import { useAuth } from '../context/AuthContext';
import jsPDF from 'jspdf';

const Statistics = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const currentYear = new Date().getFullYear();
  
  // ── Inicializar companyId directamente desde user para evitar race condition en BOSS
  const getInitialCompanyId = () => {
    if (user?.role === 'BOSS' && user.companies?.length > 0) {
      return user.companies[0].id;
    }
    return null;
  };

  const [year, setYear] = useState(currentYear);
  const [quarter, setQuarter] = useState('');
  const [geoFilter, setGeoFilter] = useState('');
  const [companyId, setCompanyId] = useState(getInitialCompanyId);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [expandedProjects, setExpandedProjects] = useState(new Set());
  const [expandedCompanies, setExpandedCompanies] = useState(new Set());
  const [availableYears, setAvailableYears] = useState([currentYear]);

  // Cargar años disponibles
  useEffect(() => {
    const loadYears = async () => {
      try {
        const response = await getAvailableYears();
        if (response.data && response.data.length > 0) {
          setAvailableYears(response.data);
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

  // Cargar empresas (solo para ADMIN — BOSS no necesita dropdown)
  useEffect(() => {
    if (user?.role !== 'ADMIN') return;
    const loadCompanies = async () => {
      try {
        const response = await getCompanies();
        setCompanies(response.data);
      } catch (error) {
        console.error('Error loading companies:', error);
      }
    };
    loadCompanies();
  }, [user]);

  // Cargar datos cuando cambia cualquier filtro
  useEffect(() => {
    loadStatistics();
  }, [year, quarter, geoFilter, companyId]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const quarterNum = quarter !== '' ? parseInt(quarter) : null;
      const geoFilterValue = geoFilter !== '' ? geoFilter : null;

      console.log('📊 Cargando estadísticas:', { year, quarter: quarterNum, geoFilter: geoFilterValue, companyId });

      const response = await getCompleteStatistics(year, quarterNum, geoFilterValue, companyId);
      setData(response.data);

      console.log('✅ Datos recibidos:', response.data);
    } catch (error) {
      console.error('❌ Error cargando estadísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleProject = (projectId) => {
    setExpandedProjects(prev => {
      const next = new Set(prev);
      next.has(projectId) ? next.delete(projectId) : next.add(projectId);
      return next;
    });
  };

  const toggleCompany = (id) => {
    setExpandedCompanies(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // ── PDF Export ─────────────────────────────────────────────
  const exportPDFReport = () => {
    if (!data || !data.foreign_breakdown || data.foreign_breakdown.length === 0) {
      alert('No hay datos internacionales para exportar');
      return;
    }

    const doc = new jsPDF();
    const { overview, foreign_breakdown } = data;
    const pdfIsAllCompanies = data.mode === 'all_companies';
    const companyLabel = pdfIsAllCompanies
      ? 'TODAS LAS EMPRESAS'
      : (data.company?.company_name || '');

    const colors = {
      primary:   [245, 158, 11],
      secondary: [59, 130, 246],
      success:   [34, 197, 94],
      company:   [124, 58, 237],
      gray:      [161, 161, 170],
      darkGray:  [82, 82, 91],
    };

    const pageHeight = doc.internal.pageSize.height;
    const pageWidth  = doc.internal.pageSize.width;
    let yPos = 20;

    const checkPageBreak = (space) => {
      if (yPos + space > pageHeight - 20) { doc.addPage(); yPos = 20; }
    };
    const drawBox = (x, y, w, h, fill) => {
      doc.setFillColor(...fill); doc.rect(x, y, w, h, 'F');
    };

    // ── HEADER ────────────────────────────────────────────────
    drawBox(0, 0, pageWidth, 50, [24, 24, 27]);
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22); doc.setFont(undefined, 'bold');
    doc.text('INFORME IVA RECLAMABLE', pageWidth / 2, 18, { align: 'center' });
    doc.setFontSize(12); doc.setFont(undefined, 'normal');
    doc.text(`Año ${year}${quarter ? ` · Q${quarter}` : ''}`, pageWidth / 2, 28, { align: 'center' });
    doc.setFontSize(10);
    doc.text(companyLabel, pageWidth / 2, 37, { align: 'center' });
    doc.setFontSize(8); doc.setTextColor(...colors.gray);
    doc.text(`Generado: ${new Date().toLocaleDateString('es-ES')}`, pageWidth / 2, 44, { align: 'center' });
    yPos = 60;
    doc.setTextColor(0, 0, 0);

    // ── RESUMEN ───────────────────────────────────────────────
    checkPageBreak(45);
    drawBox(15, yPos - 5, pageWidth - 30, 38, [254, 243, 199]);
    doc.setFontSize(12); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.primary);
    doc.text('RESUMEN GLOBAL', 20, yPos + 3);
    yPos += 10;
    doc.setFontSize(10); doc.setFont(undefined, 'normal'); doc.setTextColor(0, 0, 0);
    [
      `Total Internacional: ${overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
      `IVA Reclamable: ${overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
      `Países: ${foreign_breakdown.length}  ·  Proyectos: ${foreign_breakdown.reduce((s, c) => s + c.projects_count, 0)}`,
    ].forEach(line => { doc.text(line, 25, yPos); yPos += 7; });
    yPos += 10;

    // ── Helper: renderiza un proyecto con sus tickets ─────────
    const renderProject = (project, indent) => {
      // ← FIX: solo tickets con IVA reclamable > 0
      const tickets = (project.tickets || []).filter(t => t.foreign_tax_eur > 0);

      checkPageBreak(30);
      doc.setDrawColor(...colors.gray); doc.setLineWidth(0.2);
      doc.line(indent, yPos, pageWidth - indent, yPos);
      yPos += 5;

      doc.setFontSize(10); doc.setFont(undefined, 'bold'); doc.setTextColor(0, 0, 0);
      const splitTitle = doc.splitTextToSize(
        `${project.creative_code}  –  ${project.description}`,
        pageWidth - indent * 2 - 5
      );
      doc.text(splitTitle, indent, yPos);
      yPos += splitTitle.length * 6;

      doc.setFontSize(8); doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
      doc.text(
        `Total proyecto: ${project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
        indent + 4, yPos
      );
      yPos += 7;

      if (tickets.length > 0) {
        doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.success);
        doc.text(`TICKETS INTERNACIONALES (${tickets.length}):`, indent + 4, yPos);
        yPos += 6; doc.setTextColor(0, 0, 0);

        tickets.forEach((ticket, idx) => {
          checkPageBreak(22);
          drawBox(indent + 4, yPos - 2, pageWidth - (indent + 4) * 2, 20, [249, 250, 251]);

          doc.setFontSize(8); doc.setFont(undefined, 'bold'); doc.setTextColor(0, 0, 0);
          doc.text(`${idx + 1}. ${ticket.provider}`, indent + 7, yPos + 3);
          yPos += 7;

          doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
          doc.text(
            `Fecha: ${ticket.date || 'N/A'}  ·  Total: ${(ticket.foreign_amount || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })} ${ticket.currency}  ·  Factura: ${ticket.invoice_number || 'N/A'}`,
            indent + 7, yPos
          );
          yPos += 5;

          doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.success);
          doc.text(
            `IVA Reclamable: ${(ticket.foreign_tax_eur || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
            indent + 7, yPos
          );
          yPos += 7;
          doc.setTextColor(0, 0, 0);
        });
      }
      yPos += 4;
    };

    // ── DESGLOSE POR PAÍS ─────────────────────────────────────
    foreign_breakdown.forEach((country) => {
      checkPageBreak(50);

      // Cabecera país
      drawBox(15, yPos - 5, pageWidth - 30, 13, [219, 234, 254]);
      doc.setFontSize(12); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.secondary);
      doc.text(`${country.country_name}  (${country.currency})`, 20, yPos + 3);
      yPos += 13;
      doc.setFontSize(8); doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
      doc.text(
        `${country.geo_classification}  ·  Total: ${country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€  ·  IVA Reclamable: ${country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`,
        20, yPos
      );
      yPos += 10; doc.setTextColor(0, 0, 0);

      if (pdfIsAllCompanies && country.companies?.length > 0) {
        // ADMIN TODAS: País → Empresa → Proyectos → Tickets
        country.companies.forEach((companyGroup) => {
          checkPageBreak(18);
          drawBox(18, yPos - 3, pageWidth - 36, 12, [237, 233, 254]);
          doc.setFontSize(10); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.company);
          doc.text(`${companyGroup.company_name}`, 24, yPos + 4);
          yPos += 14; doc.setTextColor(0, 0, 0);

          companyGroup.projects.forEach(project => renderProject(project, 24));
          yPos += 4;
        });
      } else {
        // BOSS / empresa específica: País → Proyectos → Tickets
        (country.projects || []).forEach(project => renderProject(project, 20));
      }

      yPos += 8;
    });

    // ── FOOTER ────────────────────────────────────────────────
    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setDrawColor(...colors.gray); doc.setLineWidth(0.5);
      doc.line(20, pageHeight - 15, pageWidth - 20, pageHeight - 15);
      doc.setFontSize(8); doc.setFont(undefined, 'italic'); doc.setTextColor(...colors.darkGray);
      doc.text(`Página ${i} de ${totalPages}`, pageWidth / 2, pageHeight - 8, { align: 'center' });
    }

    const safeName = companyLabel.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
    doc.save(`Informe_IVA_${year}${quarter ? `_Q${quarter}` : ''}${safeName ? `_${safeName}` : ''}_${Date.now()}.pdf`);
  };

  // ── Renders de carga/vacío ──────────────────────────────────
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
  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];
  const isAllCompanies = data.mode === 'all_companies';

  // ── Componente de ticket (reutilizable) ─────────────────────
  const TicketRow = ({ ticket, projectId, isMobile }) => (
    <div
      onClick={(e) => {
        e.stopPropagation();
        navigate(`/tickets/${ticket.id}/review?filter=international&project=${projectId}`);
      }}
      className={`bg-zinc-900/50 border border-zinc-800 rounded-sm p-3 transition-colors cursor-pointer group ${
        isMobile ? 'active:border-blue-500' : 'hover:border-blue-500'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={16} className="text-zinc-600 group-hover:text-blue-400 transition-colors flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">{ticket.provider}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-zinc-600">{ticket.date}</span>
              {ticket.invoice_number && (
                <>
                  <span className="text-zinc-700">•</span>
                  <span className="text-xs text-zinc-600 font-mono">{ticket.invoice_number}</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-bold text-zinc-300">
            {ticket.final_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
          </p>
          {ticket.foreign_amount && (
            <p className="text-xs text-zinc-600">
              {ticket.foreign_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })} {ticket.currency}
            </p>
          )}
          {ticket.foreign_tax_eur && (
            <p className="text-xs text-green-500 font-semibold">
              IVA: {ticket.foreign_tax_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
            </p>
          )}
        </div>
      </div>
    </div>
  );

  // ── Componente proyecto expandible (reutilizable) ───────────
  const ProjectRow = ({ project, isMobile, indent = false }) => {
    const isExpanded = expandedProjects.has(project.id);
    // ← FIX: solo tickets con IVA reclamable > 0
    const claimableTickets = (project.tickets || []).filter(t => t.foreign_tax_eur > 0);
    return (
      <div className={`space-y-2 ${indent ? 'ml-6' : ''}`}>
        <div
          onClick={() => toggleProject(project.id)}
          className={`bg-zinc-900 border border-zinc-800 rounded-sm p-4 transition-colors cursor-pointer ${
            isMobile ? 'active:bg-zinc-800' : 'hover:border-amber-500'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {isExpanded
                ? <ChevronDown size={18} className="text-amber-500 flex-shrink-0" />
                : <ChevronRight size={18} className="text-zinc-600 flex-shrink-0" />
              }
              <div className="min-w-0">
                <p className="font-semibold text-sm text-zinc-100 mb-1 truncate">{project.description}</p>
                <div className="flex flex-col gap-1 text-xs text-zinc-500">
                  <span className="font-mono">{project.creative_code}</span>
                  <span className="bg-zinc-800 px-2 py-0.5 rounded self-start">
                    {claimableTickets.length} ticket{claimableTickets.length !== 1 ? 's' : ''} con IVA reclamable
                  </span>
                </div>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-3">
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

        {isExpanded && claimableTickets.length > 0 && (
          <div className="ml-8 space-y-2">
            <p className="text-xs text-zinc-600 font-semibold uppercase mb-2">📄 Tickets internacionales:</p>
            {claimableTickets.map(ticket => (
              <TicketRow key={ticket.id} ticket={ticket} projectId={project.id} isMobile={isMobile} />
            ))}
          </div>
        )}
      </div>
    );
  };

  // ── Render del breakdown para un país (desktop, modo TODAS) ─
  const BreakdownAllCompaniesDesktop = ({ country }) => (
    <div className="space-y-4">
      <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">
        Proyectos en {country.country_name}:
      </p>
      {(country.companies || []).map((companyGroup) => {
        const isCompanyExpanded = expandedCompanies.has(companyGroup.company_id);
        return (
          <div key={companyGroup.company_id} className="space-y-3">
            <div
              onClick={() => toggleCompany(companyGroup.company_id)}
              className="flex items-center gap-2 text-zinc-300 font-semibold bg-zinc-900/50 px-4 py-3 rounded-sm border border-zinc-800 hover:border-amber-500 cursor-pointer transition-colors"
            >
              {isCompanyExpanded
                ? <ChevronDown size={18} className="text-amber-500" />
                : <ChevronRight size={18} className="text-zinc-600" />
              }
              <Building2 size={16} className="text-amber-500" />
              <span>{companyGroup.company_name}</span>
              <span className="ml-auto text-xs text-zinc-500">
                {companyGroup.projects.length} proyecto{companyGroup.projects.length !== 1 ? 's' : ''}
              </span>
            </div>

            {isCompanyExpanded && companyGroup.projects.map(project => (
              <ProjectRow key={project.id} project={project} isMobile={false} indent />
            ))}
          </div>
        );
      })}
    </div>
  );

  // ── Render del breakdown para un país (desktop, modo empresa) ─
  const BreakdownSingleCompanyDesktop = ({ country }) => (
    <div className="space-y-3">
      <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-3">
        Proyectos con gastos en {country.country_name} ({country.currency}):
      </p>
      {(country.projects || []).map(project => (
        <ProjectRow key={project.id} project={project} isMobile={false} />
      ))}
    </div>
  );

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
            <strong className="text-zinc-300">Nacional:</strong> España peninsular + Baleares •{' '}
            <strong className="text-zinc-300">UE:</strong> Canarias + Resto Unión Europea •{' '}
            <strong className="text-zinc-300">Internacional:</strong> Resto del mundo (USD, GBP, CHF, etc.)
          </p>
        </div>

        {/* ── FILTROS ─────────────────────────────────────────── */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
          <div className={`grid grid-cols-1 ${user?.role === 'ADMIN' ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-4`}>

            {/* Año */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Año</label>
              <select
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
              >
                {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>

            {/* Trimestre */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Trimestre</label>
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

            {/* Tipo gastos — solo afecta a evolución mensual */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Tipo gastos
                <span className="ml-1 text-zinc-600 normal-case font-normal">(gráfico mensual)</span>
              </label>
              <select
                value={geoFilter}
                onChange={(e) => setGeoFilter(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
              >
                <option value="">Todos</option>
                <option value="NACIONAL">Solo nacionales (ESP)</option>
                <option value="UE">Solo UE</option>
                <option value="INTERNACIONAL">Solo internacionales</option>
              </select>
            </div>

            {/* Empresa — solo ADMIN */}
            {user?.role === 'ADMIN' && (
              <div>
                <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Empresa</label>
                <select
                  value={companyId || ''}
                  onChange={(e) => setCompanyId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none"
                >
                  <option value="">TODAS LAS EMPRESAS</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.name}{c.cif && ` (${c.cif})`}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* ── CARDS PRINCIPALES ────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <DollarSign size={32} className="text-amber-500" />
              <TrendingUp size={20} className="text-green-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Total Gastado {year}</p>
            <p className="text-3xl font-bold text-amber-500 mb-1">
              {overview.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">Nacional + Internacional</p>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Globe size={32} className="text-blue-400" />
              <TrendingUp size={20} className="text-green-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Gastos Internacionales</p>
            <p className="text-3xl font-bold text-blue-400 mb-1">
              {overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">UE + Resto mundo</p>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <Building2 size={32} className="text-green-400" />
              <div className="bg-green-500/20 px-2 py-1 rounded text-xs font-bold text-green-400">RECLAMABLE</div>
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">IVA Reclamable</p>
            <p className="text-3xl font-bold text-green-400 mb-1">
              {overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
            </p>
            <p className="text-xs text-zinc-400">Internacional recuperable</p>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 size={32} className="text-purple-400" />
            </div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Proyectos</p>
            <p className="text-3xl font-bold text-purple-400 mb-1">{overview.projects_total}</p>
            <p className="text-xs text-zinc-400">{overview.projects_closed} cerrados, {overview.projects_open} en curso</p>
          </div>
        </div>

        {/* ── GRÁFICOS ──────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Evolución mensual — filtra por geo_filter, nunca por trimestre */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
              <TrendingUp size={20} className="text-amber-500" />
              Evolución Gastos Mensual
            </h3>
            <p className="text-xs text-zinc-600 mb-6">
              Año completo{geoFilter ? ` · ${geoFilter}` : ''}
            </p>

            {monthly_evolution && monthly_evolution.some(m => m.total > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={monthly_evolution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis dataKey="month_name" stroke="#71717a" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                  <YAxis stroke="#71717a" tick={{ fill: '#a1a1aa', fontSize: 12 }}
                    tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '4px', color: '#f4f4f5' }}
                    formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 'Total']}
                  />
                  <Line type="monotone" dataKey="total" stroke="#f59e0b" strokeWidth={3}
                    dot={{ fill: '#f59e0b', r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center">
                <div className="text-center">
                  <p className="text-zinc-500 text-lg mb-2">📊</p>
                  <p className="text-zinc-500">No hay datos{geoFilter ? ` (${geoFilter})` : ''} en {year}</p>
                </div>
              </div>
            )}
          </div>

          {/* Distribución por origen — filtra por trimestre y geo_filter */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
            <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
              <Globe size={20} className="text-amber-500" />
              Distribución por Origen
            </h3>
            <p className="text-xs text-zinc-600 mb-6">
              {quarter ? `Q${quarter}` : 'Año completo'}
            </p>

            {currency_distribution && currency_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={currency_distribution}
                    cx="50%" cy="50%"
                    labelLine={false}
                    label={({ label, percentage }) => `${label} (${percentage}%)`}
                    outerRadius={100} dataKey="total"
                  >
                    {currency_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '4px', color: '#f4f4f5' }}
                    formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€`, 'Total']}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center">
                <div className="text-center">
                  <p className="text-zinc-500 text-lg mb-2">🌍</p>
                  <p className="text-zinc-500">No hay gastos registrados{quarter ? ` en Q${quarter}` : ''} de {year}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── FOREIGN BREAKDOWN ─────────────────────────────────── */}
        {foreign_breakdown && foreign_breakdown.length > 0 && (
          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-2 border-blue-500/30 rounded-sm p-4 sm:p-8">

            {/* Header */}
            <div className="mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-blue-400 mb-2">GASTOS INTERNACIONALES</h2>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="bg-amber-500 text-zinc-950 text-xs font-bold px-3 py-1 rounded">IVA RECLAMABLE</span>
                    <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">{year}</span>
                    {quarter && <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded">Q{quarter}</span>}
                    {isAllCompanies && <span className="bg-zinc-700 text-zinc-300 text-xs font-bold px-3 py-1 rounded">TODAS LAS EMPRESAS</span>}
                  </div>
                </div>
                {/* Botón exportar — solo desktop */}
                <button
                  onClick={exportPDFReport}
                  className="hidden sm:flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-2 rounded-sm text-sm font-bold transition-colors"
                >
                  <Download size={16} />
                  Exportar Informe IVA
                </button>
              </div>
            </div>

            {/* Mini stats */}
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
                  {foreign_breakdown.reduce((sum, c) => sum + c.projects_count, 0)}
                </p>
              </div>
              <div className="bg-zinc-900 border border-amber-500/30 rounded-sm p-3 sm:p-4">
                <p className="text-xs text-amber-300 font-semibold uppercase mb-1">Países</p>
                <p className="text-xl sm:text-2xl font-bold text-amber-400">{foreign_breakdown.length}</p>
              </div>
            </div>

            {/* Botón exportar — solo móvil */}
            <div className="sm:hidden mb-6">
              <button
                onClick={exportPDFReport}
                className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-3 rounded-sm text-sm font-bold transition-colors"
              >
                <Download size={16} />
                Exportar Informe IVA
              </button>
            </div>

            {/* ── VISTA MÓVIL ─────────────────────────────────── */}
            <div className="sm:hidden space-y-4">
              {foreign_breakdown.map((country) => (
                <div key={country.country_code} className="bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">

                  {/* Cabecera del país — siempre visible, no clickeable */}
                  <div className="p-4 border-b border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-blue-400 text-lg">📍</span>
                      <span className="font-semibold text-lg">{country.country_name}</span>
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        country.geo_classification === 'UE' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                      }`}>{country.geo_classification}</span>
                      <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs font-semibold">{country.currency}</span>
                    </div>
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

                  {/* Contenido — siempre visible */}
                  <div className="bg-zinc-950 p-4 space-y-3">
                    {isAllCompanies && country.companies ? (
                      // Modo TODAS: empresa → proyectos
                      country.companies.map((companyGroup) => {
                        const isCompanyExpanded = expandedCompanies.has(`mobile_${companyGroup.company_id}`);
                        return (
                          <div key={companyGroup.company_id} className="space-y-2">
                            <div
                              onClick={() => toggleCompany(`mobile_${companyGroup.company_id}`)}
                              className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-2 rounded-sm active:border-amber-500 cursor-pointer"
                            >
                              {isCompanyExpanded
                                ? <ChevronDown size={16} className="text-amber-500" />
                                : <ChevronRight size={16} className="text-zinc-600" />
                              }
                              <Building2 size={14} className="text-amber-500" />
                              <span className="text-sm font-semibold">{companyGroup.company_name}</span>
                              <span className="ml-auto text-xs text-zinc-500">{companyGroup.projects.length} proy.</span>
                            </div>
                            {isCompanyExpanded && companyGroup.projects.map(project => (
                              <ProjectRow key={project.id} project={project} isMobile indent />
                            ))}
                          </div>
                        );
                      })
                    ) : (
                      // Modo empresa específica / BOSS
                      (country.projects || []).map(project => (
                        <ProjectRow key={project.id} project={project} isMobile />
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* ── VISTA DESKTOP ───────────────────────────────── */}
            <div className="hidden sm:block bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">

              <div className="bg-zinc-800 px-6 py-4 border-b border-zinc-700">
                <h3 className="font-semibold">Desglose por País/Divisa</h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-zinc-800/50">
                    <tr className="border-b border-zinc-700">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">País/Región</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Divisa</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">Total Gastado</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">IVA Reclamable</th>
                      <th className="px-6 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">Proyectos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {foreign_breakdown.map((country) => (
                      <>
                        {/* Fila país — siempre visible, sin click */}
                        <tr key={country.country_code} className="border-b border-zinc-800 bg-zinc-900/30">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <span className="text-blue-400">📍</span>
                              <span className="font-semibold text-zinc-100">{country.country_name}</span>
                              <span className={`text-xs px-2 py-1 rounded ml-1 ${
                                country.geo_classification === 'UE' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                              }`}>{country.geo_classification}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs font-semibold">{country.currency}</span>
                          </td>
                          <td className="px-6 py-4 text-right font-semibold">
                            {country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                          </td>
                          <td className="px-6 py-4 text-right">
                            <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-sm font-bold">
                              {country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center font-semibold">{country.projects_count}</td>
                        </tr>

                        {/* Fila de proyectos — siempre visible */}
                        <tr className="bg-zinc-950">
                          <td colSpan="5" className="px-12 py-6">
                            {isAllCompanies && country.companies
                              ? <BreakdownAllCompaniesDesktop country={country} />
                              : <BreakdownSingleCompanyDesktop country={country} />
                            }
                          </td>
                        </tr>
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Mensaje cuando no hay datos internacionales */}
        {(!foreign_breakdown || foreign_breakdown.length === 0) && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8 text-center">
            <p className="text-zinc-500 text-lg mb-2">🌍</p>
            <p className="text-zinc-500">No hay gastos internacionales registrados en {year}{quarter ? ` (Q${quarter})` : ''}</p>
          </div>
        )}

      </main>
    </div>
  );
};

export default Statistics;
