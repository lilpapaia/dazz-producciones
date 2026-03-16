import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Save, UserX, Link2, Mail, ExternalLink, Check, Download } from 'lucide-react';
import { getSupplier, updateSupplier, deactivateSupplier, assignOC, addSupplierNote, getAllInvoices, getNotifications } from '../../services/suppliersApi';

const PILL = {
  PENDING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  OC_PENDING: 'bg-zinc-700/50 text-zinc-400 border-zinc-700',
  APPROVED: 'bg-green-400/10 text-green-400 border-green-400/20',
  PAID: 'bg-green-300/10 text-green-300 border-green-300/20',
  REJECTED: 'bg-red-400/10 text-red-400 border-red-400/20',
  DELETE_REQUESTED: 'bg-red-300/10 text-red-300 border-red-300/20',
};

const HISTORY_DOT = {
  NEW_INVOICE: 'bg-blue-400', REGISTRATION: 'bg-green-400', APPROVED: 'bg-green-400',
  PAID: 'bg-green-300', REJECTED: 'bg-red-400', DELETED: 'bg-red-400',
  OC_LINKED: 'bg-purple-400', IA_REJECTED: 'bg-amber-500',
};

const SupplierDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [supplier, setSupplier] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => {
    Promise.all([
      getSupplier(id),
      getAllInvoices({ supplier_id: id }),
      getNotifications({ limit: 20 }),
    ]).then(([s, inv, notifs]) => {
      setSupplier(s.data);
      setInvoices(inv.data || []);
      // Filter notifications related to this supplier
      setHistory((notifs.data || []).filter(n => n.related_supplier_id === parseInt(id)));
    }).catch(() => navigate('/suppliers/list'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleDeactivate = async () => {
    if (!confirm('Deactivate this supplier? All their tokens will be invalidated.')) return;
    await deactivateSupplier(id);
    load();
  };

  const handleAddNote = async () => {
    if (!note.trim()) return;
    setSaving(true);
    await addSupplierNote(id, note);
    setNote('');
    load();
    setSaving(false);
  };

  const timeAgo = (d) => {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return new Date(d).toLocaleDateString('en-GB');
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!supplier) return null;

  const initials = supplier.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div>
      <button onClick={() => navigate('/suppliers/list')} className="flex items-center gap-1 text-xs text-zinc-500 hover:text-amber-400 mb-3 transition-colors">
        <ChevronLeft size={14} /> Back to list
      </button>

      <div className="grid lg:grid-cols-[260px_1fr] gap-3.5">
        {/* Left: Supplier card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
          <div className="w-11 h-11 bg-amber-500 rounded-md flex items-center justify-center font-['Bebas_Neue'] text-lg text-zinc-950 mb-3">{initials}</div>
          <div className="font-['Bebas_Neue'] text-base tracking-wide text-zinc-100">{supplier.name.toUpperCase()}</div>
          <div className="text-[11px] text-zinc-500 mb-2.5 flex gap-1.5 flex-wrap items-center">
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${supplier.supplier_type === 'INFLUENCER' ? 'bg-purple-400/10 text-purple-400 border border-purple-400/20' : supplier.supplier_type === 'MIXED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-blue-400/10 text-blue-400 border border-blue-400/20'}`}>
              {supplier.supplier_type}
            </span>
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${supplier.is_active ? 'bg-green-400/10 text-green-400 border border-green-400/20' : 'bg-zinc-700/50 text-zinc-500 border border-zinc-700'}`}>
              {supplier.status}
            </span>
          </div>

          {supplier.oc_number && (
            <div className="mb-3 inline-flex items-center gap-1.5 bg-purple-400/[.08] text-purple-400 text-[11px] font-medium px-2.5 py-1 rounded border border-purple-400/15 font-mono">
              <Link2 size={11} />{supplier.oc_number}
            </div>
          )}

          <hr className="border-white/[.04] my-2" />

          {/* Data rows */}
          {[
            ['Company', supplier.company_name || 'All'],
            ['Email', supplier.email, false, true],
            ['Phone', supplier.phone],
            ['Address', supplier.address],
            ['IBAN', supplier.iban, true],
            ['Bank cert', supplier.bank_cert_url ? 'pdf' : null],
            ['Registered', supplier.created_at ? new Date(supplier.created_at).toLocaleDateString('en-GB') : '—', true],
          ].map(([label, val, mono, amber]) => (
            <div key={label} className="flex justify-between py-1.5 border-b border-white/[.04] last:border-0 text-xs">
              <span className="text-zinc-500">{label}</span>
              {val === 'pdf' ? (
                <span className="text-red-400 cursor-pointer flex items-center gap-1">View PDF <ExternalLink size={9} /></span>
              ) : (
                <span className={`text-right max-w-[155px] break-all ${mono ? 'font-mono text-[11px]' : ''} ${amber ? 'text-amber-400' : 'text-zinc-300'}`}>
                  {val || '—'}
                </span>
              )}
            </div>
          ))}

          {/* Notes */}
          {supplier.notes_internal && (
            <div className="bg-zinc-800 rounded p-2.5 text-[11px] text-zinc-400 mt-3 border-l-2 border-amber-500 whitespace-pre-wrap">
              {supplier.notes_internal}
            </div>
          )}

          <hr className="border-white/[.04] my-3" />

          {/* Event history (S1) */}
          {history.length > 0 && (
            <div className="mb-3">
              <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-2">Event history</div>
              {history.slice(0, 5).map(h => (
                <div key={h.id} className="flex items-start gap-2 py-1.5 border-b border-white/[.04] last:border-0 text-[11px]">
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1 ${HISTORY_DOT[h.event_type] || 'bg-zinc-600'}`} />
                  <div>
                    <div className="text-zinc-300">{h.message || h.title}</div>
                    <div className="text-zinc-600">{timeAgo(h.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Add note */}
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Add internal note..."
            rows={2}
            className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[11px] px-2.5 py-2 rounded focus:border-amber-500 outline-none resize-none"
          />
          <div className="flex gap-1.5 mt-1.5 flex-wrap">
            <button onClick={handleAddNote} disabled={saving || !note.trim()} className="text-[11px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded border border-zinc-700 transition-colors disabled:opacity-40 flex items-center gap-1">
              <Save size={11} /> Add note
            </button>
            {supplier.email && (
              <a href={`mailto:${supplier.email}`} className="text-[11px] bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded border border-zinc-700 transition-colors flex items-center gap-1">
                <Mail size={11} /> Email
              </a>
            )}
            {supplier.is_active && (
              <button onClick={handleDeactivate} className="text-[11px] text-red-400 border border-red-400/25 hover:bg-red-400/[.08] px-3 py-1.5 rounded transition-colors flex items-center gap-1">
                <UserX size={11} /> Deactivate
              </button>
            )}
          </div>
        </div>

        {/* Right: Invoice history */}
        <div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <div className="font-['Bebas_Neue'] text-sm tracking-wider text-zinc-300 mb-3">Invoices ({invoices.length})</div>

            {invoices.length === 0 ? (
              <p className="text-xs text-zinc-600">No invoices yet</p>
            ) : (
              <div className="space-y-1">
                {invoices.map(inv => (
                  <div key={inv.id} className="flex items-center gap-2.5 px-3 py-2.5 rounded hover:bg-white/[.02] cursor-pointer transition-colors">
                    <div className="w-7 h-7 bg-red-400/[.08] rounded flex items-center justify-center border border-red-400/[.12] flex-shrink-0">
                      <svg className="w-3.5 h-3.5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-zinc-200 font-mono flex items-center gap-1.5">
                        {inv.invoice_number}
                        {/* IA badge (S5) */}
                        <span className="text-[9px] text-green-400 flex items-center gap-0.5"><Check size={9} strokeWidth={2} />ok</span>
                      </div>
                      <div className="text-[10px] text-zinc-500">
                        {inv.oc_number && <span className="text-[9px] px-1 py-[1px] rounded bg-amber-500/[.08] text-amber-400 font-mono border border-amber-500/15 mr-1">{inv.oc_number}</span>}
                        {inv.date}
                      </div>
                    </div>
                    <div className="font-mono text-xs font-medium text-zinc-200 mx-2">{inv.final_total?.toFixed(2)} EUR</div>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${PILL[inv.status] || PILL.PENDING}`}>
                      <span className={`w-1 h-1 rounded-full ${inv.status === 'PAID' ? 'bg-green-300' : inv.status === 'APPROVED' ? 'bg-green-400' : inv.status === 'REJECTED' ? 'bg-red-400' : 'bg-amber-500'}`} />
                      {inv.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Export button (S6) */}
          {invoices.length > 0 && (
            <div className="flex justify-end mt-2">
              <button className="text-[11px] text-zinc-500 hover:text-zinc-300 border border-zinc-700 hover:border-zinc-500 px-3 py-1.5 rounded transition-colors flex items-center gap-1.5">
                <Download size={12} /> Export to Excel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplierDetail;
