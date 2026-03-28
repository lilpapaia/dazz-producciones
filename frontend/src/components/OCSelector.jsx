import { useState, useEffect } from 'react';
import { getOCPrefixes, validateOC } from '../services/suppliersApi';
import { getCompanies } from '../services/api';
import { AlertTriangle, Check } from 'lucide-react';

const labelCls = 'text-[9px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block';
const inputCls = 'w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2 rounded focus:border-amber-500 outline-none';

/**
 * OCSelector — 3-step OC builder (Company → Prefix → Number)
 *
 * Props:
 *   companyId       — pre-selected company ID (skips step 1 if set)
 *   permanentOnly   — only show permanent_oc=true prefixes (for SupplierInvite)
 *   onSelect(oc)    — called with the full OC string when valid
 *   onClear()       — called when selection is reset
 */
const OCSelector = ({ companyId: externalCompanyId, permanentOnly = false, onSelect, onClear }) => {
  const [companies, setCompanies] = useState([]);
  const [prefixes, setPrefixes] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(externalCompanyId || '');
  const [selectedPrefix, setSelectedPrefix] = useState(null);
  const [ocDigits, setOcDigits] = useState('');
  const [validation, setValidation] = useState(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    if (!permanentOnly) getCompanies().then(r => setCompanies(r.data)).catch(() => {});
    getOCPrefixes(permanentOnly).then(r => {
      setPrefixes(r.data);
      if (permanentOnly && r.data.length > 0) setSelectedPrefix(r.data[0].prefix);
    }).catch(() => {});
  }, [permanentOnly]);

  // Sync external companyId
  useEffect(() => {
    if (externalCompanyId) {
      setSelectedCompany(externalCompanyId);
      setSelectedPrefix(null);
      setOcDigits('');
      setValidation(null);
      onClear?.();
    }
  }, [externalCompanyId]);

  const filteredPrefixes = prefixes.filter(p =>
    !selectedCompany || p.company_id === parseInt(selectedCompany)
  );

  const prefixData = selectedPrefix ? prefixes.find(p => p.prefix === selectedPrefix) : null;
  const numberDigits = prefixData?.number_digits || 3;
  const yearFormat = prefixData?.year_format || '2026';

  const buildOC = (digits) => {
    if (!selectedPrefix || !digits) return '';
    return `OC-${selectedPrefix}${yearFormat}${digits.padStart(numberDigits, '0')}`;
  };

  const fullOC = buildOC(ocDigits);

  const handleDigitsChange = (value) => {
    const clean = value.replace(/\D/g, '').slice(0, numberDigits);
    setOcDigits(clean);
    setValidation(null);
    if (clean.length === numberDigits) {
      const oc = buildOC(clean);
      setValidating(true);
      validateOC(oc)
        .then(r => {
          setValidation(r.data);
          if (r.data.valid) onSelect?.(oc);
        })
        .catch(() => setValidation(null))
        .finally(() => setValidating(false));
    } else {
      onClear?.();
    }
  };

  const handlePrefixChange = (prefix) => {
    setSelectedPrefix(prefix || null);
    setOcDigits('');
    setValidation(null);
    onClear?.();
  };

  const handleCompanyChange = (companyId) => {
    setSelectedCompany(companyId);
    setSelectedPrefix(null);
    setOcDigits('');
    setValidation(null);
    onClear?.();
  };

  return (
    <div className="space-y-2">
      {/* Step 1: Company (hidden if pre-selected or permanentOnly) */}
      {!externalCompanyId && !permanentOnly && (
        <div>
          <label className={labelCls}>Empresa</label>
          <select value={selectedCompany} onChange={e => handleCompanyChange(e.target.value)} className={inputCls}>
            <option value="">Seleccionar empresa</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      )}

      {/* Step 2: Prefix (hidden if permanentOnly — auto-selected) */}
      {!permanentOnly && (selectedCompany || externalCompanyId) && (
        <div>
          <label className={labelCls}>Prefijo OC</label>
          <select value={selectedPrefix || ''} onChange={e => handlePrefixChange(e.target.value)} className={inputCls}>
            <option value="">Seleccionar prefijo</option>
            {filteredPrefixes.map(p => (
              <option key={p.prefix} value={p.prefix}>{p.prefix} — {p.description}</option>
            ))}
          </select>
        </div>
      )}

      {/* Step 3: Number + preview */}
      {selectedPrefix && (
        <div>
          <label className={labelCls}>Numero</label>
          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500 font-mono text-[13px] flex-shrink-0">OC-{selectedPrefix}{yearFormat}</span>
            <input
              value={ocDigits}
              onChange={e => handleDigitsChange(e.target.value)}
              placeholder={'0'.repeat(numberDigits)}
              maxLength={numberDigits}
              className="bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-2 py-2 rounded focus:border-amber-500 outline-none font-mono w-20"
            />
          </div>
          {ocDigits && ocDigits.length < numberDigits && !validating && (
            <div className="text-[11px] text-zinc-500 mt-1">Introduce {numberDigits} dígitos ({ocDigits.length}/{numberDigits})</div>
          )}
          {validating && <span className="text-[11px] text-zinc-500 mt-1">Verificando...</span>}
          {validation && !validation.valid && (
            <div className="text-[11px] text-red-400 mt-1 flex items-center gap-1">
              <AlertTriangle size={11} /> {validation.message}
            </div>
          )}
          {validation && validation.valid && (
            <div className="text-[11px] text-green-400 mt-1 flex items-center gap-1">
              <Check size={11} /> {fullOC} disponible
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OCSelector;
