import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadInvoice, getProfile } from '../services/api';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader2, X, ChevronLeft, User } from 'lucide-react';

const UploadPage = () => {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const mountedRef = useRef(true);
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [rejected, setRejected] = useState('');
  const [currentIdx, setCurrentIdx] = useState(-1);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getProfile().then(r => { if (mountedRef.current) setProfile(r.data); }).catch(() => {});
    return () => { mountedRef.current = false; };
  }, []);

  // BUG-54: Block navigation while uploading
  useEffect(() => {
    if (!uploading) return;
    const handler = (e) => { e.preventDefault(); e.returnValue = ''; };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [uploading]);

  const addFiles = (fileList) => {
    setRejected('');
    const all = Array.from(fileList);
    const tooBig = all.filter(f => f.size > 10 * 1024 * 1024);
    const wrongType = all.filter(f => f.type !== 'application/pdf' && f.size <= 10 * 1024 * 1024);
    const valid = all.filter(f => f.type === 'application/pdf' && f.size <= 10 * 1024 * 1024);
    if (tooBig.length) setRejected(`${tooBig.length} file(s) too large (max 10MB)`);
    else if (wrongType.length) setRejected(`${wrongType.length} file(s) rejected — only PDF accepted`);
    if (!valid.length) return;
    setFiles(prev => [...prev, ...valid.map(f => ({ id: crypto.randomUUID(), file: f, status: 'pending', result: null }))]);
  };

  const handleDrop = (e) => { e.preventDefault(); setDragOver(false); if (!uploading && e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files); };
  const removeFile = (id) => setFiles(prev => prev.filter(f => f.id !== id));

  // BUG-56: Dynamic timeout based on file size (60s base, +15s per 5MB over 5MB, max 180s)
  const getUploadTimeout = (file) => {
    const base = 60000;
    const extra = Math.max(0, file.size - 5 * 1024 * 1024) / (5 * 1024 * 1024) * 15000;
    return Math.min(base + Math.ceil(extra), 180000);
  };

  const handleUploadAll = async () => {
    setUploading(true);
    const updated = [...files];
    for (let i = 0; i < updated.length; i++) {
      if (!mountedRef.current) return;
      if (updated[i].status !== 'pending') continue;
      setCurrentIdx(i);
      updated[i].status = 'uploading';
      setFiles([...updated]);
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), getUploadTimeout(updated[i].file));
        const { data } = await uploadInvoice(updated[i].file, { signal: controller.signal });
        clearTimeout(timeoutId);
        updated[i] = { ...updated[i], status: 'success', result: data };
      } catch (err) {
        const isTimeout = err.code === 'ERR_CANCELED' || err.name === 'AbortError';
        const detail = err.response?.data?.detail;
        updated[i] = { ...updated[i], status: 'error', result: typeof detail === 'object' ? detail : { errors: [isTimeout ? 'Timeout — server did not respond in 60 seconds' : (detail || 'Upload failed')] } };
      }
      if (!mountedRef.current) return;
      setFiles([...updated]);
    }
    if (mountedRef.current) {
      setCurrentIdx(-1);
      setUploading(false);
    }
  };

  const reset = () => setFiles([]);
  const pendingCount = files.filter(f => f.status === 'pending').length;
  const allDone = files.length > 0 && files.every(f => f.status !== 'pending' && f.status !== 'uploading');
  const successCount = files.filter(f => f.status === 'success').length;
  const errorCount = files.filter(f => f.status === 'error').length;

  return (
    <div className="max-w-2xl lg:max-w-4xl mx-auto pt-4 lg:pt-6 lg:px-6">
      {/* Header */}
      <div className="px-4 lg:px-0 mb-4 flex items-center gap-3">
        <button onClick={() => { if (!uploading) navigate('/'); }} disabled={uploading} className={`lg:hidden w-8 h-8 bg-[#27272a] rounded-lg flex items-center justify-center ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
          <ChevronLeft size={16} className="text-zinc-300" strokeWidth={1.5} />
        </button>
        <h1 className="font-['Bebas_Neue'] text-[16px] lg:text-[22px] tracking-wider text-zinc-300">Upload invoice</h1>
      </div>

      {/* No IBAN — block upload */}
      {profile && !profile.iban_masked && (
        <div className="mx-4 lg:mx-0 bg-amber-500/[.06] border border-amber-500/[.12] rounded-xl p-6 text-center mb-4">
          <AlertCircle size={28} className="text-amber-400 mx-auto mb-3" strokeWidth={1.5} />
          <p className="text-sm font-medium text-zinc-200 mb-2">IBAN required</p>
          <p className="text-[12px] text-zinc-400 leading-relaxed mb-3">
            To upload invoices you need to register your IBAN and bank certificate first.
          </p>
          <button onClick={() => navigate('/profile/change-iban')}
            className="bg-amber-500 text-zinc-950 text-[12px] font-bold px-4 py-2 rounded-lg hover:bg-amber-400 transition-colors">
            Register IBAN
          </button>
        </div>
      )}

      {/* Drop zone */}
      {!allDone && (!profile || profile.iban_masked) && (
        <div
          onDragOver={e => { e.preventDefault(); if (!uploading) setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => { if (!uploading) fileRef.current?.click(); }}
          className={`mx-4 lg:mx-0 border-2 border-dashed rounded-xl p-7 lg:p-14 text-center transition-all mb-3 ${
            uploading ? 'border-zinc-800 bg-zinc-900/50 cursor-not-allowed opacity-50' :
            dragOver ? 'border-amber-500 bg-amber-500/[.03] cursor-pointer' : 'border-zinc-700 bg-white/[.01] active:border-amber-500 cursor-pointer'
          }`}
        >
          {uploading ? (
            <>
              <Loader2 size={28} className="text-amber-500 mx-auto mb-2 animate-spin" strokeWidth={1.5} />
              <p className="text-sm font-medium text-amber-400 mb-1">AI analyzing...</p>
              <p className="text-[11px] text-zinc-500">Please wait until processing completes</p>
            </>
          ) : (
            <>
              <UploadIcon size={28} className="text-zinc-600 mx-auto mb-2 lg:mb-3 lg:w-10 lg:h-10" strokeWidth={1.5} />
              <p className="text-sm lg:text-base font-medium text-zinc-300 mb-1">Select your invoice</p>
              <p className="text-[11px] lg:text-[13px] text-zinc-500">PDF only · Max 10MB · Multiple files allowed</p>
              <p className="text-[10px] text-zinc-600 mt-2 bg-[#27272a] inline-block px-2.5 py-1 rounded-md">
                AI will extract and verify all data automatically
              </p>
            </>
          )}
          <input ref={fileRef} type="file" accept=".pdf,application/pdf" multiple disabled={uploading} onChange={e => { if (e.target.files?.length) addFiles(e.target.files); e.target.value = ''; }} className="hidden" />
        </div>
      )}

      {/* Rejected files feedback */}
      {rejected && (
        <div className="mx-4 lg:mx-0 mb-3 bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-2.5 text-[12px] flex items-center gap-2">
          <AlertCircle size={13} className="flex-shrink-0" strokeWidth={1.5} />
          {rejected}
        </div>
      )}

      {/* OC info warning */}
      {!allDone && (!profile || profile.iban_masked) && (
        <div className="mx-4 lg:mx-0 mb-3 rounded-lg p-2.5 text-[11px] flex items-start gap-2 bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] leading-relaxed">
          <AlertCircle size={13} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
          Make sure your invoice includes the correct OC. AI will identify the project and company automatically.
        </div>
      )}

      {/* OC permanente (si tiene asignado) */}
      {!allDone && profile?.oc_number && (
        <div className="mx-4 lg:mx-0 mb-4">
          <div className="text-[9px] text-zinc-400 tracking-widest uppercase mb-2">Your permanent OC</div>
          <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 flex items-center gap-3">
            <User size={16} className="text-purple-400 flex-shrink-0" strokeWidth={1.5} />
            <div>
              <div className="font-['IBM_Plex_Mono'] text-xs text-purple-400">{profile.oc_number}</div>
              <div className="text-[10px] text-zinc-500 mt-0.5">Permanent OC</div>
            </div>
          </div>
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="px-4 lg:px-0 space-y-2 lg:space-y-3 mb-3">
          {files.map((f) => (
            <div key={f.id} className={`bg-[#18181b] border rounded-[10px] p-3 lg:p-4 flex items-center gap-3 ${
              f.status === 'success' ? 'border-green-400/20' :
              f.status === 'error' ? 'border-red-400/20' :
              f.status === 'uploading' ? 'border-amber-500/30' :
              'border-zinc-800'
            }`}>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                f.status === 'success' ? 'bg-green-400/10' :
                f.status === 'error' ? 'bg-red-400/10' :
                f.status === 'uploading' ? 'bg-amber-500/10' :
                'bg-red-400/[.08]'
              }`}>
                {f.status === 'success' ? <CheckCircle size={16} className="text-green-400" /> :
                 f.status === 'error' ? <AlertCircle size={16} className="text-red-400" /> :
                 f.status === 'uploading' ? <Loader2 size={16} className="text-amber-500 animate-spin" /> :
                 <FileText size={16} className="text-red-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-zinc-200 truncate">{f.file.name}</div>
                <div className="text-[10px] text-zinc-500">
                  {f.status === 'pending' && `${(f.file.size / 1024).toFixed(0)} KB`}
                  {f.status === 'uploading' && <span className="text-amber-400">Verifying with AI...</span>}
                  {f.status === 'success' && <span className="text-green-400">Uploaded — {f.result?.status || 'PENDING'}</span>}
                  {f.status === 'error' && <span className="text-red-400">{f.result?.errors?.[0] || 'Failed'}</span>}
                </div>
                {f.status === 'error' && f.result?.errors?.length > 1 && (
                  <div className="mt-1">{f.result.errors.slice(1).map((e, j) => <div key={j} className="text-[9px] text-red-400/70">— {e}</div>)}</div>
                )}
              </div>
              {f.status === 'pending' && !uploading && (
                <button onClick={() => removeFile(f.id)} className="text-zinc-600 hover:text-zinc-400 p-1"><X size={14} /></button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action */}
      {pendingCount > 0 && !uploading && (
        <div className="px-4 lg:px-0 mb-4">
          <button onClick={handleUploadAll} className="w-full bg-amber-500 text-zinc-950 font-bold text-sm py-3.5 rounded-[10px] active:bg-amber-400 transition-colors">
            Upload {pendingCount} invoice{pendingCount !== 1 ? 's' : ''} and verify with AI
          </button>
        </div>
      )}

      {allDone && (
        <div className="px-4 lg:px-0">
          <div className="text-center text-xs text-zinc-400 mb-3">
            {successCount > 0 && <span className="text-green-400">{successCount} uploaded</span>}
            {successCount > 0 && errorCount > 0 && ' · '}
            {errorCount > 0 && <span className="text-red-400">{errorCount} failed</span>}
          </div>
          <div className="flex gap-2">
            <button onClick={reset} className="flex-1 text-xs py-3 rounded-[10px] bg-[#27272a] border border-zinc-700 text-zinc-300">Upload more</button>
            <button onClick={() => navigate('/')} className="flex-1 text-xs py-3 rounded-[10px] bg-amber-500 text-zinc-950 font-bold">View invoices</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
