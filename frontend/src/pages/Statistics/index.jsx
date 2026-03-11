import { useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, TrendingUp, Globe, Building2, BarChart3 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useStatisticsData } from './hooks/useStatisticsData';
import { useExpandedState } from './hooks/useExpandedState';
import { exportPDFReport } from './services/pdfExport';
import StatCard from './components/StatCard';
import StatisticsFilters from './components/StatisticsFilters';
import MonthlyChart from './components/MonthlyChart';
import DistributionChart from './components/DistributionChart';
import CountryBreakdown from './components/CountryBreakdown';

const Statistics = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const {
    year, setYear, quarter, setQuarter, geoFilter, setGeoFilter,
    companyId, setCompanyId, companies, availableYears, loading, data,
  } = useStatisticsData(user);

  const { expandedProjects, expandedCompanies, toggleProject, toggleCompany } = useExpandedState();

  const claimableBreakdown = useMemo(
    () => data?.foreign_breakdown?.filter(c => c.tax_reclamable_eur > 0) || [],
    [data]
  );

  const handleExportPDF = useCallback(() => {
    exportPDFReport({ data, year, quarter });
  }, [data, year, quarter]);

  const handleNavigate = useCallback((path) => {
    navigate(path);
  }, [navigate]);

  if (loading) return <LoadingSpinner size="lg" fullPage message="Cargando estadisticas..." />;

  if (!data) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <p className="text-zinc-400">No hay datos disponibles</p>
      </div>
    );
  }

  const { overview, monthly_evolution, currency_distribution } = data;
  const isAllCompanies = data.mode === 'all_companies';

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">

      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <h1 className="text-4xl font-bebas tracking-wider mb-2">ESTADISTICAS</h1>
          <p className="text-zinc-400 text-sm">Analisis de gastos nacionales e internacionales</p>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* Info Box */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-sm p-4">
          <h3 className="text-blue-400 font-semibold text-sm mb-2">ℹ️ Clasificacion Geografica</h3>
          <p className="text-zinc-400 text-sm">
            <strong className="text-zinc-300">Nacional:</strong> Espana peninsular + Baleares •{' '}
            <strong className="text-zinc-300">UE:</strong> Canarias + Resto Union Europea •{' '}
            <strong className="text-zinc-300">Internacional:</strong> Resto del mundo (USD, GBP, CHF, etc.)
          </p>
        </div>

        {/* Filtros */}
        <StatisticsFilters
          year={year} setYear={setYear}
          quarter={quarter} setQuarter={setQuarter}
          geoFilter={geoFilter} setGeoFilter={setGeoFilter}
          companyId={companyId} setCompanyId={setCompanyId}
          companies={companies} availableYears={availableYears}
          userRole={user?.role}
        />

        {/* Cards principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={DollarSign} secondaryIcon={TrendingUp}
            iconColor="text-amber-500"
            label={`Total Gastado ${year}`}
            value={`${overview.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`}
            valueColor="text-amber-500"
            subtitle="Nacional + Internacional"
          />
          <StatCard
            icon={Globe} secondaryIcon={TrendingUp}
            iconColor="text-blue-400"
            label="Gastos Internacionales"
            value={`${overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`}
            valueColor="text-blue-400"
            subtitle="UE + Resto mundo"
          />
          <StatCard
            icon={Building2}
            iconColor="text-green-400"
            badge="RECLAMABLE"
            label="IVA Reclamable"
            value={`${overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`}
            valueColor="text-green-400"
            subtitle="Internacional recuperable"
          />
          <StatCard
            icon={BarChart3}
            iconColor="text-purple-400"
            label="Proyectos"
            value={overview.projects_total}
            valueColor="text-purple-400"
            subtitle={`${overview.projects_closed} cerrados, ${overview.projects_open} en curso`}
          />
        </div>

        {/* Graficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MonthlyChart data={monthly_evolution} year={year} geoFilter={geoFilter} />
          <DistributionChart data={currency_distribution} quarter={quarter} year={year} />
        </div>

        {/* Desglose internacional */}
        <CountryBreakdown
          claimableBreakdown={claimableBreakdown}
          overview={overview}
          year={year}
          quarter={quarter}
          isAllCompanies={isAllCompanies}
          expandedProjects={expandedProjects}
          expandedCompanies={expandedCompanies}
          toggleProject={toggleProject}
          toggleCompany={toggleCompany}
          onNavigate={handleNavigate}
          onExportPDF={handleExportPDF}
        />

      </main>
    </div>
  );
};

export default Statistics;
