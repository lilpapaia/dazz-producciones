import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadInvoice } from '../services/api';

const UploadPage = () => {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null); // { success, data } or { success: false, errors, warnings }

  const handleFile = (f) => {
    if (!f) return;
    if (f.type !== 'application/pdf') { alert('Only PDF files are accepted'); return; }
    if (f.size > 10 * 1024 * 1024) { alert('File too large (max 10MB)'); return; }
    setFile(f);
    setResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const { data } = await uploadInvoice(file);
      setResult({ success: true, data });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        setResult({ success: false, errors: detail.errors || [], warnings: detail.warnings || [] });
      } else {
        setResult({ success: false, errors: [detail || 'Upload failed'], warnings: [] });
      }
    } finally {
      setUploading(false);
    }
  };

  const reset = () => { setFile(null); setResult(null); };

  return (
    <div className="px-4 pt-4 max-w-lg mx-auto">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-3">Upload invoice</h1>

      {/* Success state */}
      {result?.success && (
        <div className="bg-zinc-900 border border-green-400/20 rounded-xl p-5 text-center">
          <CheckCircle size={36} className="text-green-400 mx-auto mb-2" />
          <h2 className="font-['Bebas_Neue'] text-lg text-zinc-100 mb-1">Invoice uploaded</h2>
          <p className="text-xs text-zinc-400 mb-1">
            Status: <span className="text-amber-400 font-semibold">{result.data?.status || 'PENDING'}</span>
          </p>
          {result.data?.warnings?.length > 0 && (
            <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded-md p-2.5 text-[11px] mt-2 text-left">
              {result.data.warnings.map((w, i) => <div key={i}>{w}</div>)}
            </div>
          )}
          <div className="flex gap-2 mt-4">
            <button onClick={reset} className="flex-1 text-xs py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">Upload another</button>
            <button onClick={() => navigate('/invoices')} className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs py-2.5 rounded-md transition-colors">View invoices</button>
          </div>
        </div>
      )}

      {/* Error state */}
      {result && !result.success && (
        <div className="bg-zinc-900 border border-red-400/20 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={20} className="text-red-400" />
            <h2 className="font-['Bebas_Neue'] text-base text-zinc-100">Verification failed</h2>
          </div>
          <ul className="space-y-1 mb-3">
            {result.errors.map((e, i) => (
              <li key={i} className="text-xs text-red-400 flex items-start gap-1.5">
                <span className="text-red-500 mt-0.5">-</span> {e}
              </li>
            ))}
          </ul>
          {result.warnings?.length > 0 && (
            <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded-md p-2.5 text-[11px] mb-3">
              {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
            </div>
          )}
          <button onClick={reset} className="w-full text-xs py-2.5 rounded-md border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
            Try again
          </button>
        </div>
      )}

      {/* Upload zone */}
      {!result && (
        <>
          {!file ? (
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragOver ? 'border-amber-500 bg-amber-500/[.03]' : 'border-zinc-700 hover:border-amber-500 bg-white/[.01]'
              }`}
            >
              <UploadIcon size={28} className="text-zinc-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-zinc-300 mb-1">Drop PDF here</p>
              <p className="text-[11px] text-zinc-500">or tap to select file</p>
              <p className="text-[10px] text-zinc-600 mt-2 bg-zinc-800 inline-block px-2.5 py-1 rounded">PDF only, max 10MB</p>
              <input ref={fileRef} type="file" accept=".pdf,application/pdf" onChange={e => handleFile(e.target.files?.[0])} className="hidden" />
            </div>
          ) : (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              {/* File preview */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-red-400/[.08] rounded-lg flex items-center justify-center border border-red-400/[.12]">
                  <FileText size={18} className="text-red-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-zinc-200 truncate">{file.name}</div>
                  <div className="text-[10px] text-zinc-500">{(file.size / 1024).toFixed(0)} KB</div>
                </div>
                <button onClick={reset} className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">Remove</button>
              </div>

              {uploading ? (
                <div className="text-center py-4">
                  <Loader2 size={24} className="text-amber-500 animate-spin mx-auto mb-2" />
                  <p className="text-xs text-zinc-400">Verifying with AI...</p>
                  <p className="text-[10px] text-zinc-600 mt-0.5">Extracting invoice data and validating</p>
                </div>
              ) : (
                <button
                  onClick={handleUpload}
                  className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-3 rounded-md transition-colors"
                >
                  Upload and verify
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default UploadPage;
