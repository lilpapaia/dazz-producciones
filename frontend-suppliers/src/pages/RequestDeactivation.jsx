import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestDeactivation } from '../services/api';
import { AlertTriangle, ChevronLeft } from 'lucide-react';

const RequestDeactivation = () => {
  const navigate = useNavigate();
  const [reason, setReason] = useState('');
  const [sending, setSending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!reason.trim()) return;
    setError('');
    setSending(true);
    try {
      await requestDeactivation({ reason: reason.trim() });
      setSubmitted(true);
      setTimeout(() => navigate('/profile'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit deactivation request');
    }
    setSending(false);
  };

  return (
    <div className="max-w-[480px] lg:max-w-[640px] mx-auto px-4 pt-4 lg:pt-6 lg:px-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <button onClick={() => navigate('/profile')} className="w-7 h-7 bg-zinc-800 rounded-lg flex items-center justify-center lg:hidden">
          <ChevronLeft size={14} className="text-zinc-300" />
        </button>
        <h1 className="font-['Bebas_Neue'] text-[18px] lg:text-[22px] tracking-wider text-zinc-100">Request account deactivation</h1>
      </div>

      {/* Warning */}
      <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-2.5 text-[12px] flex items-start gap-2 mb-4 leading-relaxed">
        <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
        Your account and invoice history will be retained for legal compliance (6 years, Spanish tax law). You will not be able to log in or submit invoices after deactivation.
      </div>

      {/* Form */}
      <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-4 mb-4">
        <label className="text-[10px] text-zinc-400 tracking-widest uppercase font-semibold mb-1 block">
          Reason for deactivation <span className="text-amber-500">*</span>
        </label>
        <textarea
          value={reason}
          onChange={e => setReason(e.target.value)}
          rows={4}
          placeholder="Please tell us why you want to deactivate your account..."
          className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 text-[13px] px-3 py-2.5 rounded-[7px] focus:border-amber-500 outline-none resize-none"
        />
      </div>

      {submitted && (
        <div className="bg-green-400/[.08] text-green-400 border border-green-400/[.15] rounded-lg p-3 text-[13px] mb-4 text-center font-semibold">
          Deactivation request sent
        </div>
      )}

      {error && (
        <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded-lg p-2.5 text-xs mb-3">{error}</div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={() => navigate('/profile')}
          className="flex-1 bg-zinc-800 border border-zinc-700 text-zinc-300 text-[13px] py-2.5 rounded-lg hover:bg-zinc-700 transition-colors">
          Cancel
        </button>
        <button onClick={handleSubmit} disabled={sending || !reason.trim()}
          className="flex-1 bg-red-400/15 border border-red-400/30 text-red-400 text-[13px] font-bold py-2.5 rounded-lg transition-colors disabled:opacity-40">
          {sending ? 'Sending...' : 'Send deactivation request'}
        </button>
      </div>
    </div>
  );
};

export default RequestDeactivation;
