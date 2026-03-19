import { memo } from 'react';
import { ROLES } from '../../../constants/roles';

const selectClass = "w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2 text-zinc-100 focus:border-amber-500 focus:outline-none";
const labelClass = "block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2";

const StatisticsFilters = memo(({
  year, setYear, quarter, setQuarter, geoFilter, setGeoFilter,
  companyId, setCompanyId, companies, availableYears, userRole,
}) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
    <div className={`grid grid-cols-1 ${userRole === ROLES.ADMIN ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-4`}>

      <div>
        <label className={labelClass}>Ano</label>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value))} className={selectClass}>
          {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      <div>
        <label className={labelClass}>Trimestre</label>
        <select value={quarter} onChange={(e) => setQuarter(e.target.value)} className={selectClass}>
          <option value="">Ano completo</option>
          <option value="1">Q1 (Ene-Mar)</option>
          <option value="2">Q2 (Abr-Jun)</option>
          <option value="3">Q3 (Jul-Sep)</option>
          <option value="4">Q4 (Oct-Dic)</option>
        </select>
      </div>

      <div>
        <label className={labelClass}>
          Tipo gastos
          <span className="ml-1 text-zinc-600 normal-case font-normal">(grafico mensual)</span>
        </label>
        <select value={geoFilter} onChange={(e) => setGeoFilter(e.target.value)} className={selectClass}>
          <option value="">Todos</option>
          <option value="NACIONAL">Solo nacionales (ESP)</option>
          <option value="UE">Solo UE</option>
          <option value="INTERNACIONAL">Solo internacionales</option>
        </select>
      </div>

      {userRole === ROLES.ADMIN && (
        <div>
          <label className={labelClass}>Empresa</label>
          <select
            value={companyId || ''}
            onChange={(e) => setCompanyId(e.target.value ? parseInt(e.target.value) : null)}
            className={selectClass}
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
));

StatisticsFilters.displayName = 'StatisticsFilters';

export default StatisticsFilters;
