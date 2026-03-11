import { memo } from 'react';
import { Download } from 'lucide-react';
import CountryMobileCard from './CountryMobileCard';
import CountryDesktopTable from './CountryDesktopTable';

const CountryBreakdown = memo(({
  claimableBreakdown, overview, year, quarter, isAllCompanies,
  expandedProjects, expandedCompanies, toggleProject, toggleCompany,
  onNavigate, onExportPDF,
}) => {
  if (!claimableBreakdown || claimableBreakdown.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8 text-center">
        <p className="text-zinc-500 text-lg mb-2">🌍</p>
        <p className="text-zinc-500">No hay gastos internacionales registrados en {year}{quarter ? ` (Q${quarter})` : ''}</p>
      </div>
    );
  }

  return (
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
          <button
            onClick={onExportPDF}
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
            {overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
          </p>
        </div>
        <div className="bg-zinc-900 border border-green-500/30 rounded-sm p-3 sm:p-4">
          <p className="text-xs text-green-300 font-semibold uppercase mb-1">IVA Reclamable</p>
          <p className="text-xl sm:text-2xl font-bold text-green-400">
            {overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
          </p>
        </div>
        <div className="bg-zinc-900 border border-purple-500/30 rounded-sm p-3 sm:p-4">
          <p className="text-xs text-purple-300 font-semibold uppercase mb-1">Proyectos</p>
          <p className="text-xl sm:text-2xl font-bold text-purple-400">
            {claimableBreakdown.reduce((sum, c) => sum + c.projects_count, 0)}
          </p>
        </div>
        <div className="bg-zinc-900 border border-amber-500/30 rounded-sm p-3 sm:p-4">
          <p className="text-xs text-amber-300 font-semibold uppercase mb-1">Pa&iacute;ses</p>
          <p className="text-xl sm:text-2xl font-bold text-amber-400">{claimableBreakdown.length}</p>
        </div>
      </div>

      {/* Boton exportar movil */}
      <div className="sm:hidden mb-6">
        <button
          onClick={onExportPDF}
          className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-4 py-3 rounded-sm text-sm font-bold transition-colors"
        >
          <Download size={16} />
          Exportar Informe IVA
        </button>
      </div>

      {/* Vista movil */}
      <div className="sm:hidden space-y-4">
        {claimableBreakdown.map((country) => (
          <CountryMobileCard
            key={country.country_code}
            country={country}
            isAllCompanies={isAllCompanies}
            expandedProjects={expandedProjects}
            expandedCompanies={expandedCompanies}
            toggleProject={toggleProject}
            toggleCompany={toggleCompany}
            onNavigate={onNavigate}
          />
        ))}
      </div>

      {/* Vista desktop */}
      <CountryDesktopTable
        claimableBreakdown={claimableBreakdown}
        isAllCompanies={isAllCompanies}
        expandedProjects={expandedProjects}
        expandedCompanies={expandedCompanies}
        toggleProject={toggleProject}
        toggleCompany={toggleCompany}
        onNavigate={onNavigate}
      />
    </div>
  );
});

CountryBreakdown.displayName = 'CountryBreakdown';

export default CountryBreakdown;
