import { memo } from 'react';
import { ChevronDown, ChevronRight, Building2 } from 'lucide-react';
import ProjectRow from './ProjectRow';

const CountryMobileCard = memo(({ country, isAllCompanies, expandedProjects, expandedCompanies, toggleProject, toggleCompany, onNavigate }) => (
  <div className="bg-zinc-900 border border-zinc-700 rounded-sm overflow-hidden">
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
          <p className="font-semibold">{country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;</p>
        </div>
        <div className="text-right">
          <p className="text-zinc-500 text-xs">IVA Reclamable</p>
          <p className="text-green-400 font-bold">{country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}&euro;</p>
        </div>
        <div className="text-right">
          <p className="text-zinc-500 text-xs">Proyectos</p>
          <p className="font-semibold">{country.projects_count}</p>
        </div>
      </div>
    </div>

    <div className="bg-zinc-950 p-4 space-y-3">
      {isAllCompanies && country.companies ? (
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
                <ProjectRow
                  key={project.id}
                  project={project}
                  isMobile
                  indent
                  isExpanded={expandedProjects.has(project.id)}
                  onToggle={toggleProject}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          );
        })
      ) : (
        (country.projects || []).map(project => (
          <ProjectRow
            key={project.id}
            project={project}
            isMobile
            isExpanded={expandedProjects.has(project.id)}
            onToggle={toggleProject}
            onNavigate={onNavigate}
          />
        ))
      )}
    </div>
  </div>
));

CountryMobileCard.displayName = 'CountryMobileCard';

export default CountryMobileCard;
