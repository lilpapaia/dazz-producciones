import { memo } from 'react';
import { ChevronDown, ChevronRight, Building2 } from 'lucide-react';
import ProjectRow from './ProjectRow';

const BreakdownAllCompanies = ({ country, expandedProjects, expandedCompanies, toggleProject, toggleCompany, onNavigate }) => (
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
            <ProjectRow
              key={project.id}
              project={project}
              isMobile={false}
              indent
              isExpanded={expandedProjects.has(project.id)}
              onToggle={toggleProject}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      );
    })}
  </div>
);

const BreakdownSingleCompany = ({ country, expandedProjects, toggleProject, onNavigate }) => (
  <div className="space-y-3">
    <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-3">
      Proyectos con gastos en {country.country_name} ({country.currency}):
    </p>
    {(country.projects || []).map(project => (
      <ProjectRow
        key={project.id}
        project={project}
        isMobile={false}
        isExpanded={expandedProjects.has(project.id)}
        onToggle={toggleProject}
        onNavigate={onNavigate}
      />
    ))}
  </div>
);

const CountryDesktopTable = memo(({ claimableBreakdown, isAllCompanies, expandedProjects, expandedCompanies, toggleProject, toggleCompany, onNavigate }) => (
  <div className="hidden sm:block bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">
    <div className="bg-zinc-800 px-6 py-4 border-b border-zinc-700">
      <h3 className="font-semibold">Desglose por Pa&iacute;s/Divisa</h3>
    </div>

    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-zinc-800/50">
          <tr className="border-b border-zinc-700">
            <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Pa&iacute;s/Regi&oacute;n</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">Divisa</th>
            <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">Total Gastado</th>
            <th className="px-6 py-3 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider">IVA Reclamable</th>
            <th className="px-6 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">Proyectos</th>
          </tr>
        </thead>
        <tbody>
          {claimableBreakdown.map((country) => (
            <CountryTableRows
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
        </tbody>
      </table>
    </div>
  </div>
));

const CountryTableRows = ({ country, isAllCompanies, expandedProjects, expandedCompanies, toggleProject, toggleCompany, onNavigate }) => (
  <>
    <tr className="border-b border-zinc-800 bg-zinc-900/30">
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
        {country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
      </td>
      <td className="px-6 py-4 text-right">
        <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-sm font-bold">
          {country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;
        </span>
      </td>
      <td className="px-6 py-4 text-center font-semibold">{country.projects_count}</td>
    </tr>
    <tr className="bg-zinc-950">
      <td colSpan="5" className="px-12 py-6">
        {isAllCompanies && country.companies
          ? <BreakdownAllCompanies
              country={country}
              expandedProjects={expandedProjects}
              expandedCompanies={expandedCompanies}
              toggleProject={toggleProject}
              toggleCompany={toggleCompany}
              onNavigate={onNavigate}
            />
          : <BreakdownSingleCompany
              country={country}
              expandedProjects={expandedProjects}
              toggleProject={toggleProject}
              onNavigate={onNavigate}
            />
        }
      </td>
    </tr>
  </>
);

CountryDesktopTable.displayName = 'CountryDesktopTable';

export default CountryDesktopTable;
