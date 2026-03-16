import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react';
import { uploadInvoice } from '../services/api';

const UploadPage = () => {
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [files, setFiles] = useState([]); // Array of { file, status, result }
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(-1);

  const addFiles = (fileList) => {
    const newFiles = Array.from(fileList)
      .filter(f => f.type === 'application/pdf' && f.size <= 10 * 1024 * 1024)
      .map(f => ({ file: f, status: 'pending', result: null }));
    if (newFiles.length === 0) return;
    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
  };

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUploadAll = async () => {
    setUploading(true);
    const updated = [...files];

    for (let i = 0; i < updated.length; i++) {
      if (updated[i].status !== 'pending') continue;
      setCurrentIdx(i);
      updated[i].status = 'uploading';
      setFiles([...updated]);

      try {
        const { data } = await uploadInvoice(updated[i].file);
        updated[i].status = 'success';
        updated[i].result = data;
      } catch (err) {
        const detail = err.response?.data?.detail;
        updated[i].status = 'error';
        if (typeof detail === 'object') {
          updated[i].result = { errors: detail.errors || [], warnings: detail.warnings || [] };
        } else {
          updated[i].result = { errors: [detail || 'Upload failed'], warnings: [] };
        }
      }
      setFiles([...updated]);
    }

    setCurrentIdx(-1);
    setUploading(false);
  };

  const reset = () => { setFiles([]); setCurrentIdx(-1); };
  const hasResults = files.some(f => f.status === 'success' || f.status === 'error');
  const allDone = files.length > 0 && files.every(f => f.status !== 'pending' && f.status !== 'uploading');
  const successCount = files.filter(f => f.status === 'success').length;
  const errorCount = files.filter(f => f.status === 'error').length;

  return (
    <div className="px-4 pt-4 max-w-lg mx-auto">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-3">Upload invoices</h1>

      {/* Drop zone (always visible if no results yet) */}
      {!hasResults && (
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all mb-3 ${
            dragOver ? 'border-amber-500 bg-amber-500/[.03]' : 'border-zinc-700 hover:border-amber-500 bg-white/[.01]'
          }`}
        >
          <UploadIcon size={28} className="text-zinc-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-zinc-300 mb-1">Drop PDFs here</p>
          <p className="text-[11px] text-zinc-500">or tap to select files (multiple allowed)</p>
          <p className="text-[10px] text-zinc-600 mt-2 bg-zinc-800 inline-block px-2.5 py-1 rounded">PDF only, max 10MB each</p>
          <input ref={fileRef} type="file" accept=".pdf,application/pdf" multiple onChange={e => { if (e.target.files?.length) addFiles(e.target.files); e.target.value = ''; }} className="hidden" />
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2 mb-3">
          {files.map((f, i) => (
            <div key={i} className={`bg-zinc-900 border rounded-xl p-3 flex items-center gap-3 ${
              f.status === 'success' ? 'border-green-400/20' :
              f.status === 'error' ? 'border-red-400/20' :
              f.status === 'uploading' ? 'border-amber-500/30' :
              'border-zinc-800'
            }`}>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                f.status === 'success' ? 'bg-green-400/10' :
                f.status === 'error' ? 'bg-red-400/10' :
                f.status === 'uploading' ? 'bg-amber-500/10' :
                'bg-red-400/[.08] border border-red-400/[.12]'
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
                  {f.status === 'uploading' && 'Verifying with AI...'}
                  {f.status === 'success' && <span className="text-green-400">Uploaded — {f.result?.status || 'PENDING'}</span>}
                  {f.status === 'error' && <span className="text-red-400">{f.result?.errors?.[0] || 'Failed'}</span>}
                </div>
                {f.status === 'error' && f.result?.errors?.length > 1 && (
                  <div className="mt-1 space-y-0.5">
                    {f.result.errors.slice(1).map((e, j) => (
                      <div key={j} className="text-[10px] text-red-400/80">- {e}</div>
                    ))}
                  </div>
                )}
              </div>
              {f.status === 'pending' && !uploading && (
                <button onClick={() => removeFile(i)} className="text-zinc-600 hover:text-zinc-400 p-1"><X size={14} /></button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      {files.length > 0 && !allDone && !uploading && (
        <button
          onClick={handleUploadAll}
          className="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm py-3 rounded-xl transition-colors"
        >
          Upload {files.filter(f => f.status === 'pending').length} invoice{files.filter(f => f.status === 'pending').length !== 1 ? 's' : ''}
        </button>
      )}

      {allDone && (
        <div className="space-y-2">
          <div className="text-center text-xs text-zinc-400 mb-2">
            {successCount > 0 && <span className="text-green-400">{successCount} uploaded</span>}
            {successCount > 0 && errorCount > 0 && ' · '}
            {errorCount > 0 && <span className="text-red-400">{errorCount} failed</span>}
          </div>
          <div className="flex gap-2">
            <button onClick={reset} className="flex-1 text-xs py-2.5 rounded-xl border border-zinc-700 text-zinc-400 hover:bg-zinc-800 transition-colors">
              Upload more
            </button>
            <button onClick={() => navigate('/invoices')} className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs py-2.5 rounded-xl transition-colors">
              View invoices
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
