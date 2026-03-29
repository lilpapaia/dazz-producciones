import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, requestDataChange } from '../services/api';
import { Info, ChevronLeft } from 'lucide-react';

const EditData = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');

  useEffect(() => {
    getProfile().then(r => {
      setProfile(r.data);
      setName(r.data.name || '');
      setPhone(r.data.phone || '');
      setAddress(r.data.address || '');
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleSubmit = async () => {
    setSending(true);
    try {
      await requestDataChange({ name: name.trim(), phone: phone.trim(), address: address.trim() });
      navigate('/profile');
    } catch { /* error handled by interceptor */ }
    setSending(false);
  };

  const hasChanges = profile && (name.trim() !== (profile.name || '') || phone.trim() !== (profile.phone || '') || address.trim() !== (profile.address || ''));

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const inputCls = "w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2.5 rounded-[7px] focus:border-amber-500 outline-none";
  const labelCls = "text-[10px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block";

  return (
    <div className="max-w-[500px] mx-auto px-4 pt-4 lg:pt-0">
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <button onClick={() => navigate('/profile')} className="w-7 h-7 bg-zinc-800 rounded-lg flex items-center justify-center lg:hidden">
          <ChevronLeft size={14} className="text-zinc-300" />
        </button>
        <h1 className="font-['Bebas_Neue'] text-[18px] tracking-wider text-zinc-100">Edit my data</h1>
      </div>
      <p className="text-[12px] text-zinc-500 mb-4">Changes require admin approval before taking effect</p>

      {/* Info */}
      <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded-lg p-2.5 text-[12px] flex items-start gap-2 mb-4 leading-relaxed">
        <Info size={12} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
        Email and NIF/CIF cannot be changed. Contact admin@dazzcreative.com for assistance.
      </div>

      {/* Form */}
      <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-4 mb-4">
        <div className="mb-3">
          <label className={labelCls}>Name / Company</label>
          <input value={name} onChange={e => setName(e.target.value)} className={inputCls} />
        </div>
        <div className="mb-3">
          <label className={labelCls}>Phone</label>
          <input value={phone} onChange={e => setPhone(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Fiscal address</label>
          <input value={address} onChange={e => setAddress(e.target.value)} className={inputCls} />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={() => navigate('/profile')}
          className="flex-1 bg-zinc-800 border border-zinc-700 text-zinc-300 text-[13px] py-2.5 rounded-lg hover:bg-zinc-700 transition-colors">
          Cancel
        </button>
        <button onClick={handleSubmit} disabled={sending || !hasChanges}
          className="flex-1 bg-amber-500 hover:bg-amber-400 text-zinc-950 text-[13px] font-bold py-2.5 rounded-lg transition-colors disabled:opacity-50">
          {sending ? 'Submitting...' : 'Submit for review'}
        </button>
      </div>
    </div>
  );
};

export default EditData;
