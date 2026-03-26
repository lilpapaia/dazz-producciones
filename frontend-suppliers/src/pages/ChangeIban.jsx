import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestIbanChange } from '../services/api';
import { AlertTriangle, FileText, X, ChevronLeft } from 'lucide-react';

const ChangeIban = () => {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [newIban, setNewIban] = useState('');
  const [file, setFile] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!newIban.trim() || !file) return;
    if (file.type !== 'application/pdf') { setError('Only PDF files are accepted'); return; }
    if (file.size > 10 * 1024 * 1024) { setError('File size must be under 10MB'); return; }
    setError('');
    setSending(true);
    try {
      await requestIbanChange(newIban.trim(), file);
      navigate('/profile');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit IBAN change request');
    } finally {
      setSending(false);
    }
  };

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2.5 rounded-[7px] focus:border-amber-500 outline-none";
  const labelCls = "text-[10px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div className="max-w-[500px] mx-auto px-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <button onClick={() => navigate('/profile')} className="w-7 h-7 bg-zinc-800 rounded-lg flex items-center justify-center lg:hidden">
          <ChevronLeft size={14} className="text-zinc-300" />
        </button>
        <h1 className="font-['Bebas_Neue'] text-[18px] tracking-wider text-zinc-100">Change IBAN & bank certificate</h1>
      </div>
      <p className="text-[12px] text-zinc-500 mb-4">For security, changes require admin approval</p>

      {/* Warning */}
      <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded-lg p-2.5 text-[12px] flex items-start gap-2 mb-4 leading-relaxed">
        <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
        Your current IBAN will remain active until admin approves the change. Invoices will continue to be validated against the current IBAN.
      </div>

      {/* Form */}
      <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-4 mb-4">
        <div className="mb-3">
          <label className={labelCls}>New IBAN <span className="text-amber-500">*</span></label>
          <input value={newIban} onChange={e => setNewIban(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''))} placeholder="ES1212345678901234567890"
            className={`${inputCls} font-['IBM_Plex_Mono']`} />
          <div className="text-[11px] text-zinc-600 mt-1">Must match the IBAN on the bank certificate — AI will verify</div>
        </div>
        <div>
          <label className={labelCls}>New bank certificate (PDF) <span className="text-amber-500">*</span></label>
          {file ? (
            <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-[8px] p-3">
              <FileText size={16} className="text-red-400 flex-shrink-0" />
              <span className="text-xs text-zinc-300 truncate flex-1">{file.name}</span>
              <button onClick={() => setFile(null)} className="text-zinc-600 hover:text-zinc-400"><X size={14} /></button>
            </div>
          ) : (
            <div onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-zinc-700 rounded-[8px] p-5 text-center cursor-pointer hover:border-amber-500 transition-colors">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto mb-2 text-zinc-600">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
              </svg>
              <div className="text-[12px] text-zinc-400">Select PDF</div>
            </div>
          )}
          <input ref={fileRef} type="file" accept=".pdf,application/pdf" onChange={e => { if (e.target.files?.[0]) setFile(e.target.files[0]); e.target.value = ''; }} className="hidden" />
          <div className="text-[11px] text-zinc-600 mt-1">The AI will verify that the IBAN on the certificate matches the one entered above</div>
        </div>
      </div>

      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-2.5 text-xs mb-3">{error}</div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={() => navigate('/profile')}
          className="flex-1 bg-zinc-800 border border-zinc-700 text-zinc-300 text-[13px] py-2.5 rounded-lg hover:bg-zinc-700 transition-colors">
          Cancel
        </button>
        <button onClick={handleSubmit} disabled={sending || !newIban.trim() || !file}
          className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 text-[13px] font-bold py-2.5 rounded-lg transition-colors disabled:opacity-50">
          {sending ? 'Submitting...' : 'Submit for review'}
        </button>
      </div>
    </div>
  );
};

export default ChangeIban;
