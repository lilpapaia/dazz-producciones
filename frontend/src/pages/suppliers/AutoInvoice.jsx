import { useState, useEffect, useRef } from 'react';
import { Search, FileText, Send, Download, Check, X } from 'lucide-react';
import { getCompanies } from '../../services/api';
import OCSelector from '../../components/OCSelector';
import { getNextInvoiceNumber, searchSuppliersForAutoinvoice, generateAutoinvoice, previewAutoinvoice } from '../../services/suppliersApi';
import { showError } from '../../utils/toast';
import useClickOutside from '../../hooks/useClickOutside';

const AutoInvoice = () => {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [companyInfo, setCompanyInfo] = useState(null);

  // Supplier search
  const [supplierSearch, setSupplierSearch] = useState('');
  const [supplierResults, setSupplierResults] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const searchRef = useRef(null);
  useClickOutside(searchRef, () => setSupplierResults([]));

  // Editable supplier fields (pre-filled from autocomplete)
  const [supplierName, setSupplierName] = useState('');
  const [supplierNif, setSupplierNif] = useState('');
  const [supplierAddress, setSupplierAddress] = useState('');
  const [supplierIban, setSupplierIban] = useState('');

  // Invoice details
  const [concept, setConcept] = useState('');
  const [baseAmount, setBaseAmount] = useState('');
  const [ivaPercent, setIvaPercent] = useState('21');
  const [irpfPercent, setIrpfPercent] = useState('0');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' }));
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [ocNumber, setOcNumber] = useState('');

  const [sending, setSending] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confirmation, setConfirmation] = useState(null);
  const [selectedPrefixPermanent, setSelectedPrefixPermanent] = useState(false);

  useEffect(() => {
    getCompanies().then(r => setCompanies(r.data)).catch(() => {});
  }, []);

  // Fetch next invoice number when company changes
  useEffect(() => {
    if (!companyId) { setCompanyInfo(null); setInvoiceNumber(''); return; }
    getNextInvoiceNumber(companyId).then(r => {
      setCompanyInfo(r.data);
      setInvoiceNumber(r.data.invoice_number);
    }).catch(() => {});
  }, [companyId]);

  // Supplier autocomplete with debounce
  useEffect(() => {
    if (supplierSearch.length < 2) { setSupplierResults([]); return; }
    const timer = setTimeout(() => {
      searchSuppliersForAutoinvoice(supplierSearch).then(r => setSupplierResults(r.data)).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [supplierSearch]);

  const selectSupplier = (s) => {
    setSelectedSupplier(s);
    setSupplierName(s.name);
    setSupplierNif(s.nif_cif || '');
    setSupplierAddress(s.address || '');
    setSupplierIban(s.iban || '');
    setSupplierSearch(s.name);
    setSupplierResults([]);
  };

  // Calculations
  const base = parseFloat(baseAmount) || 0;
  const ivaPct = parseFloat(ivaPercent) / 100;
  const irpfPct = parseFloat(irpfPercent) / 100;
  const ivaAmount = Math.round(base * ivaPct * 100) / 100;
  const irpfAmount = Math.round(base * irpfPct * 100) / 100;
  const total = Math.round((base + ivaAmount - irpfAmount) * 100) / 100;

  const canSubmit = companyId && selectedSupplier && concept.trim() && base > 0 && invoiceNumber.trim() && ocNumber.trim() && invoiceDate.trim();

  const buildPayload = () => ({
    company_id: parseInt(companyId),
    supplier_id: selectedSupplier.id,
    invoice_number: invoiceNumber.trim(),
    date: invoiceDate.trim(),
    concept: concept.trim(),
    base_amount: base,
    iva_percentage: ivaPct,
    irpf_percentage: irpfPct,
    oc_number: ocNumber.trim(),
  });

  const handlePreview = async () => {
    if (!canSubmit) return;
    setPreviewing(true);
    try {
      const res = await previewAutoinvoice(buildPayload());
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setShowPreview(true);
    } catch (e) { showError(e.response?.data?.detail || 'Error generating preview'); }
    setPreviewing(false);
  };

  const handleGenerate = async () => {
    if (!canSubmit) return;
    setSending(true);
    try {
      const { data } = await generateAutoinvoice(buildPayload());
      setShowPreview(false);
      if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }
      setConfirmation({
        supplierName: data.supplier_name,
        ocNumber: data.oc_number,
        pdfUrl: data.file_url,
        invoiceNumber: data.invoice_number,
        finalTotal: data.final_total,
      });
    } catch (e) { showError(e.response?.data?.detail || 'Error generating invoice'); }
    setSending(false);
  };

  const resetForm = () => {
    setConfirmation(null);
    setSelectedSupplier(null); setSupplierSearch(''); setSupplierName(''); setSupplierNif('');
    setSupplierAddress(''); setSupplierIban(''); setConcept(''); setBaseAmount(''); setOcNumber('');
    setSelectedPrefixPermanent(false);
    if (companyId) getNextInvoiceNumber(companyId).then(r => setInvoiceNumber(r.data.invoice_number)).catch(() => {});
  };

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2.5 rounded focus:border-amber-500 outline-none";
  const labelCls = "text-[10px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div>
      {confirmation ? (
        <div className="max-w-[500px] mx-auto mt-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-8 text-center">
            <div className="w-14 h-14 bg-green-400/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check size={28} className="text-green-400" />
            </div>
            <h2 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-1">Autofactura generada</h2>
            <div className="text-[13px] text-zinc-400 mb-4">
              <div>{confirmation.supplierName}</div>
              <div className="font-mono text-amber-400 mt-1">{confirmation.ocNumber}</div>
              <div className="font-mono text-zinc-300 text-[15px] mt-2">{confirmation.invoiceNumber} · {confirmation.finalTotal?.toFixed(2)} EUR</div>
            </div>
            <div className="flex flex-col gap-2 max-w-[280px] mx-auto">
              <button onClick={async () => {
                try {
                  const res = await fetch(confirmation.pdfUrl);
                  const blob = await res.blob();
                  const a = document.createElement('a');
                  a.href = URL.createObjectURL(blob);
                  a.download = `${confirmation.invoiceNumber}.pdf`;
                  document.body.appendChild(a); a.click(); a.remove();
                  URL.revokeObjectURL(a.href);
                } catch { showError('Error descargando PDF'); }
              }} className="w-full text-[13px] bg-zinc-800 border border-zinc-700 text-zinc-300 py-2.5 rounded hover:bg-zinc-700 transition-colors flex items-center justify-center gap-2">
                <Download size={14} /> Descargar PDF
              </button>
              <button onClick={resetForm}
                className="w-full text-[13px] bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold py-2.5 rounded transition-colors flex items-center justify-center gap-2">
                ← Nueva autofactura
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
      <h1 className="font-['Bebas_Neue'] text-[22px] tracking-wider text-zinc-100 mb-3">Nueva autofactura</h1>

      <div className="bg-green-400/[.06] text-green-400 border border-green-400/[.12] rounded p-2.5 text-[13px] mb-4 flex items-start gap-2 max-w-[700px]">
        <FileText size={14} className="flex-shrink-0 mt-0.5" />
        El PDF se genera automáticamente, se sube a Cloudinary y se envía por email al proveedor.
      </div>

      <div className="grid lg:grid-cols-[1fr_320px] gap-3.5 max-w-[900px]">
        {/* LEFT: Form */}
        <div className="space-y-3">
          {/* Empresa emisora */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Empresa emisora</div>
            <div className="mb-2">
              <label className={labelCls}>Empresa DAZZ *</label>
              <select value={companyId} onChange={e => setCompanyId(e.target.value)} className={`${inputCls} appearance-none`}>
                <option value="">Seleccionar empresa</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <div className="text-[11px] text-zinc-600 mt-1">Los datos fiscales del emisor se autocompletan según la empresa</div>
            </div>
            {companyInfo && (
              <div className="bg-zinc-800 rounded-[7px] p-2.5 text-[12px] text-zinc-400">
                <div className="font-semibold text-zinc-300 mb-1">{companyInfo.company_name}</div>
                <div>CIF: {companyInfo.company_cif || '—'} · {companyInfo.company_address || '—'}</div>
              </div>
            )}
          </div>

          {/* Proveedor receptor */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Proveedor receptor</div>
            <div className="mb-3 relative" ref={searchRef}>
              <label className={labelCls}>Buscar proveedor *</label>
              <div className="relative">
                <Search size={13} className="absolute left-2.5 top-3 text-zinc-500 pointer-events-none" />
                <input
                  value={supplierSearch}
                  onChange={e => { setSupplierSearch(e.target.value); if (selectedSupplier) setSelectedSupplier(null); }}
                  placeholder="Nombre o NIF..."
                  className={`${inputCls} pl-8`}
                />
              </div>
              {supplierResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded-md overflow-hidden z-50 shadow-xl">
                  {supplierResults.map(s => (
                    <div key={s.id} onClick={() => selectSupplier(s)}
                      className="px-3 py-2 hover:bg-zinc-800 cursor-pointer text-xs border-b border-white/[.04] last:border-0 flex items-center gap-2">
                      <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center text-[9px] font-bold text-zinc-950 font-['Bebas_Neue'] flex-shrink-0">
                        {s.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-[13px] text-zinc-200">{s.name}</div>
                        <div className="text-[11px] text-zinc-500">{s.nif_cif || '—'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {selectedSupplier && (
              <div className="grid grid-cols-2 gap-2">
                <div><label className={labelCls}>Nombre *</label><input value={supplierName} onChange={e => setSupplierName(e.target.value)} className={inputCls} /></div>
                <div><label className={labelCls}>NIF/CIF *</label><input value={supplierNif} onChange={e => setSupplierNif(e.target.value)} className={`${inputCls} font-mono`} /></div>
                <div><label className={labelCls}>Dirección *</label><input value={supplierAddress} onChange={e => setSupplierAddress(e.target.value)} className={inputCls} /></div>
                <div><label className={labelCls}>IBAN *</label><input value={supplierIban} onChange={e => setSupplierIban(e.target.value)} className={`${inputCls} font-mono`} /></div>
              </div>
            )}
          </div>

          {/* Detalles factura */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Detalles de la factura</div>
            <div className="mb-2">
              <label className={labelCls}>Concepto *</label>
              <input value={concept} onChange={e => setConcept(e.target.value)} placeholder="Servicios de creación de contenido · Campaña Nike Q4 2026" className={inputCls} />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div><label className={labelCls}>Importe base *</label><input type="number" step="0.01" value={baseAmount} onChange={e => setBaseAmount(e.target.value)} placeholder="1520.00" className={`${inputCls} font-mono`} /></div>
              <div>
                <label className={labelCls}>IVA % *</label>
                <select value={ivaPercent} onChange={e => setIvaPercent(e.target.value)} className={`${inputCls} appearance-none`}>
                  <option value="21">21%</option><option value="10">10%</option><option value="4">4%</option><option value="0">0%</option>
                </select>
              </div>
              <div>
                <label className={labelCls}>IRPF % *</label>
                <select value={irpfPercent} onChange={e => setIrpfPercent(e.target.value)} className={`${inputCls} appearance-none`}>
                  <option value="0">0%</option><option value="7">7%</option><option value="15">15%</option><option value="19">19%</option>
                </select>
              </div>
              <div><label className={labelCls}>Fecha *</label><input value={invoiceDate} onChange={e => setInvoiceDate(e.target.value)} className={inputCls} /></div>
              <div><label className={labelCls}>Nº Factura *</label><input value={invoiceNumber} onChange={e => setInvoiceNumber(e.target.value)} className={`${inputCls} font-mono`} /></div>
              <div><label className={labelCls}>OC *</label>
                <OCSelector companyId={companyId ? parseInt(companyId) : null} allowExisting onSelect={(oc, prefixData) => { setOcNumber(oc); setSelectedPrefixPermanent(!!prefixData?.permanent_oc); }} onClear={() => { setOcNumber(''); setSelectedPrefixPermanent(false); }} />
              </div>
            </div>
            {selectedPrefixPermanent && selectedSupplier?.last_invoice_number && (
              <div className="text-[11px] text-zinc-500 mt-2 flex items-center gap-1">
                <span>💡</span> Última registrada: <span className="font-mono text-zinc-400">{selectedSupplier.last_invoice_number}</span>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Summary */}
        <div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 font-semibold">Resumen</div>
            <div className="flex justify-between py-2 border-b border-white/[.04] text-xs">
              <span className="text-zinc-500">Base imponible</span>
              <span className="text-zinc-200 font-mono">{base.toFixed(2)} EUR</span>
            </div>
            <div className="flex justify-between py-2 border-b border-white/[.04] text-xs">
              <span className="text-zinc-500">IVA ({ivaPercent}%)</span>
              <span className="text-zinc-200 font-mono">{ivaAmount.toFixed(2)} EUR</span>
            </div>
            {irpfAmount > 0 && (
              <div className="flex justify-between py-2 border-b border-white/[.04] text-xs">
                <span className="text-zinc-500">IRPF ({irpfPercent}%)</span>
                <span className="text-red-400 font-mono">-{irpfAmount.toFixed(2)} EUR</span>
              </div>
            )}
            <div className="flex justify-between pt-3 mt-1 border-t border-zinc-700 mb-4">
              <span className="text-[13px] font-semibold text-zinc-300">Total</span>
              <span className="font-mono text-[17px] font-bold text-amber-400">{total.toFixed(2)} EUR</span>
            </div>
            <button onClick={handlePreview} disabled={!canSubmit || previewing}
              className="w-full text-[13px] text-zinc-300 border border-zinc-700 py-2.5 rounded hover:bg-zinc-800 transition-colors disabled:opacity-40 mb-1.5">
              {previewing ? 'Generating...' : 'Vista previa PDF'}
            </button>
            <button onClick={handleGenerate} disabled={!canSubmit || sending}
              className="w-full text-[13px] bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold py-2.5 rounded transition-colors disabled:opacity-40 flex items-center justify-center gap-2">
              <Send size={13} />
              {sending ? 'Generating...' : 'Generar y enviar'}
            </button>
            {selectedSupplier && (
              <div className="text-[11px] text-zinc-600 text-center mt-2">
                Se enviará por email a {selectedSupplier.email} y aparecerá en su portal
              </div>
            )}
          </div>
        </div>
      </div>
        </>
      )}

      {/* Preview lightbox */}
      {showPreview && previewUrl && (
        <div className="fixed inset-0 bg-black z-50 flex flex-col"
          style={{ minHeight: '100dvh', paddingTop: 'env(safe-area-inset-top, 0px)', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
            <span className="text-sm text-zinc-300 font-mono">{invoiceNumber}</span>
            <button onClick={() => { setShowPreview(false); URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }}
              className="text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700">
              <X size={20} />
            </button>
          </div>
          <div className="flex-1 min-h-0">
            <iframe src={previewUrl} className="w-full h-full bg-white" title="Preview autofactura" />
          </div>
          <div className="bg-zinc-900 border-t border-zinc-800 px-6 py-4 flex items-center justify-center">
            <button onClick={handleGenerate} disabled={sending}
              className="text-[13px] bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold px-8 py-2.5 rounded transition-colors disabled:opacity-40 flex items-center justify-center gap-2">
              <Send size={13} />
              {sending ? 'Generating...' : 'Generar y enviar →'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutoInvoice;
