import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyDocuments, getLegalDocument, getLegalDocDownloadUrl, acceptDocument } from '../services/api';
import { FileText, CheckCircle, AlertCircle, Download, X, ChevronLeft, Loader2 } from 'lucide-react';
import useEscapeKey from '../hooks/useEscapeKey';

const DocumentModal = ({ doc, onAccept, onClose }) => {
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const scrollRef = useRef(null);

  useEscapeKey(onClose);

  // Auto-enable if content is short enough
  useEffect(() => {
    const el = scrollRef.current;
    if (el && el.scrollHeight <= el.clientHeight + 20) {
      setHasScrolledToBottom(true);
    }
  }, []);

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollTop + clientHeight >= scrollHeight - 20) {
      setHasScrolledToBottom(true);
    }
  };

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await acceptDocument(doc.id);
      onAccept(doc.id);
      onClose();
    } catch {
      setAccepting(false);
    }
  };

  const handleDownload = async () => {
    if (!doc.file_url) return;
    setDownloading(true);
    try {
      const { data } = await getLegalDocDownloadUrl(doc.id);
      window.open(data.url, '_blank');
    } catch { /* ignore */ }
    setDownloading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-zinc-900 rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100">{doc.title}</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body — scrollable HTML content */}
        <div ref={scrollRef} onScroll={handleScroll} className="max-h-[60vh] overflow-y-auto px-6 py-4">
          {doc.content ? (
            <div dangerouslySetInnerHTML={{ __html: doc.content }} />
          ) : (
            <p className="text-zinc-500 text-sm">No content available for this document.</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800">
          {doc.file_url ? (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="inline-flex items-center gap-1.5 border border-zinc-700 text-zinc-300 text-xs px-3.5 py-2 rounded-md hover:bg-zinc-800 transition-colors disabled:opacity-50"
            >
              {downloading ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
              Download PDF
            </button>
          ) : (
            <div />
          )}
          <div className="flex items-center gap-2">
            {!hasScrolledToBottom && (
              <span className="text-zinc-500 text-[10px]">(scroll to read)</span>
            )}
            <button onClick={onClose} className="text-zinc-400 text-xs px-4 py-2 hover:text-zinc-200 transition-colors">
              Later
            </button>
            <button
              onClick={handleAccept}
              disabled={!hasScrolledToBottom || accepting}
              className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs px-5 py-2 rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-1.5"
            >
              {accepting && <Loader2 size={13} className="animate-spin" />}
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const Documents = () => {
  const navigate = useNavigate();
  const [docs, setDocs] = useState(null);
  const [error, setError] = useState('');
  const [modalDoc, setModalDoc] = useState(null);
  const [loadingDoc, setLoadingDoc] = useState(null);

  const fetchDocs = useCallback(() => {
    getMyDocuments()
      .then(r => setDocs(r.data))
      .catch(() => setError('Failed to load documents'));
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  const openDocument = async (docId) => {
    setLoadingDoc(docId);
    try {
      const { data } = await getLegalDocument(docId);
      setModalDoc(data);
    } catch {
      setError('Failed to load document');
    }
    setLoadingDoc(null);
  };

  const handleAccepted = (docId) => {
    // Move from pending to accepted
    setDocs(prev => {
      if (!prev) return prev;
      const accepted_doc = prev.pending.find(d => d.id === docId);
      if (!accepted_doc) return prev;
      return {
        pending: prev.pending.filter(d => d.id !== docId),
        accepted: [...prev.accepted, { ...accepted_doc, accepted_at: new Date().toISOString() }],
      };
    });
  };

  const downloadAccepted = async (docId) => {
    try {
      const { data } = await getLegalDocDownloadUrl(docId);
      window.open(data.url, '_blank');
    } catch { /* ignore */ }
  };

  if (!docs && !error) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl lg:max-w-4xl mx-auto pt-4 lg:pt-6 lg:px-6">
      {/* Header */}
      <div className="px-4 lg:px-0 mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/')} className="lg:hidden w-8 h-8 bg-[#27272a] rounded-lg flex items-center justify-center">
          <ChevronLeft size={16} className="text-zinc-300" strokeWidth={1.5} />
        </button>
        <h1 className="font-['Bebas_Neue'] text-[16px] lg:text-[22px] tracking-wider text-zinc-300">Legal documents</h1>
      </div>

      {error && (
        <div className="mx-4 lg:mx-0 mb-4 bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-3 text-xs flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Pending */}
      {docs?.pending?.length > 0 && (
        <div className="px-4 lg:px-0 mb-6">
          <div className="text-[9px] text-amber-400 tracking-widest uppercase mb-3 flex items-center gap-2">
            <AlertCircle size={12} />
            Pending acceptance ({docs.pending.length})
          </div>
          <div className="space-y-2">
            {docs.pending.map(doc => (
              <div key={doc.id} className="bg-[#18181b] border border-amber-500/20 rounded-[10px] p-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <FileText size={16} className="text-amber-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-zinc-200 truncate">{doc.title}</div>
                  <div className="text-[10px] text-zinc-500">Version {doc.version}</div>
                </div>
                <button
                  onClick={() => openDocument(doc.id)}
                  disabled={loadingDoc === doc.id}
                  className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-[11px] px-4 py-2 rounded-md transition-colors disabled:opacity-50 flex items-center gap-1.5 flex-shrink-0"
                >
                  {loadingDoc === doc.id ? <Loader2 size={12} className="animate-spin" /> : null}
                  Review & Accept
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No pending */}
      {docs?.pending?.length === 0 && (
        <div className="mx-4 lg:mx-0 mb-6 bg-green-400/[.04] border border-green-400/[.12] rounded-xl p-5 text-center">
          <CheckCircle size={24} className="text-green-400 mx-auto mb-2" />
          <p className="text-sm font-medium text-zinc-200">All documents accepted</p>
          <p className="text-[11px] text-zinc-500 mt-1">You have no pending legal documents</p>
        </div>
      )}

      {/* Accepted */}
      {docs?.accepted?.length > 0 && (
        <div className="px-4 lg:px-0 mb-6">
          <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-3 flex items-center gap-2">
            <CheckCircle size={12} className="text-green-400" />
            Accepted ({docs.accepted.length})
          </div>
          <div className="space-y-2">
            {docs.accepted.map(doc => (
              <div key={doc.id} className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-green-400/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle size={16} className="text-green-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-zinc-200 truncate">{doc.title}</div>
                  <div className="text-[10px] text-zinc-500">
                    Accepted {new Date(doc.accepted_at).toLocaleDateString('en-GB')}
                  </div>
                </div>
                <button
                  onClick={() => downloadAccepted(doc.id)}
                  className="border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 text-[11px] px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 flex-shrink-0"
                >
                  <Download size={12} /> PDF
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal */}
      {modalDoc && (
        <DocumentModal
          doc={modalDoc}
          onAccept={handleAccepted}
          onClose={() => setModalDoc(null)}
        />
      )}
    </div>
  );
};

export default Documents;
