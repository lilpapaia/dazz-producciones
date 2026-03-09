import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const CompanyMultiSelect = ({ selectedCompanyIds = [], onChange, companies = [], label = "Empresas" }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = (companyId) => {
    if (selectedCompanyIds.includes(companyId)) {
      // Remover
      onChange(selectedCompanyIds.filter(id => id !== companyId));
    } else {
      // Añadir
      onChange([...selectedCompanyIds, companyId]);
    }
  };

  const handleRemove = (companyId) => {
    onChange(selectedCompanyIds.filter(id => id !== companyId));
  };

  const selectedCompanies = companies.filter(c => selectedCompanyIds.includes(c.id));
  const availableCompanies = companies.filter(c => !selectedCompanyIds.includes(c.id));

  return (
    <div>
      <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
        {label.toUpperCase()}
      </label>

      {/* Chips de empresas seleccionadas */}
      {selectedCompanies.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedCompanies.map(company => (
            <div
              key={company.id}
              className="flex items-center gap-2 bg-amber-500/20 border border-amber-500/30 text-amber-400 px-3 py-1.5 rounded-sm text-sm"
            >
              <span>{company.name}</span>
              <button
                onClick={() => handleRemove(company.id)}
                className="hover:bg-amber-500/30 rounded-sm p-0.5 transition-colors"
                type="button"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Dropdown para añadir empresas */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500 text-left flex items-center justify-between"
        >
          <span className="text-zinc-400">
            {selectedCompanies.length === 0
              ? 'Seleccionar empresas...'
              : `${selectedCompanies.length} empresa${selectedCompanies.length > 1 ? 's' : ''} seleccionada${selectedCompanies.length > 1 ? 's' : ''}`
            }
          </span>
          <svg
            className={`w-5 h-5 text-zinc-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Dropdown menu */}
        {isOpen && (
          <div className="absolute z-10 mt-2 w-full bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-60 overflow-y-auto">
            {companies.length === 0 ? (
              <div className="px-4 py-3 text-sm text-zinc-500">
                No hay empresas disponibles
              </div>
            ) : (
              companies.map(company => (
                <button
                  key={company.id}
                  type="button"
                  onClick={() => handleToggle(company.id)}
                  className="w-full px-4 py-3 text-left hover:bg-zinc-800 transition-colors flex items-center justify-between group"
                >
                  <div className="flex-1">
                    <p className="text-sm text-zinc-100">{company.name}</p>
                    {company.cif && (
                      <p className="text-xs text-zinc-500 font-mono mt-0.5">CIF: {company.cif}</p>
                    )}
                  </div>
                  
                  {/* Checkbox */}
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                    selectedCompanyIds.includes(company.id)
                      ? 'bg-amber-500 border-amber-500'
                      : 'border-zinc-600 group-hover:border-zinc-500'
                  }`}>
                    {selectedCompanyIds.includes(company.id) && (
                      <svg className="w-3 h-3 text-zinc-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {selectedCompanies.length === 0 && (
        <p className="text-xs text-zinc-500 mt-2">
          ⚠️ Usuario sin empresas no podrá crear proyectos
        </p>
      )}
    </div>
  );
};

export default CompanyMultiSelect;
