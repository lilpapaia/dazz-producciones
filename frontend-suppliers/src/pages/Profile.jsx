import { useState, useEffect } from 'react';
import { getProfile } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Shield, ExternalLink } from 'lucide-react';

const Profile = () => {
  const { supplier } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile().then(r => setProfile(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!profile) return null;

  const initials = profile.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  const TYPE_BADGE = {
    INFLUENCER: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
    GENERAL: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
    MIXED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Title */}
      <div className="px-4 mb-3 flex items-center justify-between">
        <h1 className="font-['Bebas_Neue'] text-[18px] tracking-wider text-zinc-100">My data</h1>
        <div className="w-8 h-8 rounded-full bg-amber-500/15 flex items-center justify-center text-[11px] font-bold text-amber-400 font-['Bebas_Neue']">
          {initials}
        </div>
      </div>

      {/* Contact admin banner */}
      <div className="mx-4 mb-4 rounded-lg p-2.5 text-[11px] flex items-start gap-2 bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] leading-relaxed">
        <Shield size={13} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
        To update any data, contact admin@dazzcreative.com
      </div>

      {/* Avatar + name + badges */}
      <div className="px-4 mb-4">
        <div className="w-14 h-14 bg-amber-500 rounded-xl flex items-center justify-center font-['Bebas_Neue'] text-[22px] text-zinc-950 mb-3">
          {initials}
        </div>
        <div className="font-['Bebas_Neue'] text-[18px] tracking-wide text-zinc-100 mb-1">
          {profile.name?.toUpperCase()}
        </div>
        <div className="flex gap-1.5 mb-3 flex-wrap">
          <span className="text-[9px] font-bold px-2 py-[2px] rounded bg-green-400/10 text-green-400 border border-green-400/20">
            ACTIVE
          </span>
          <span className={`text-[9px] font-bold px-2 py-[2px] rounded border ${TYPE_BADGE[profile.supplier_type] || TYPE_BADGE.GENERAL}`}>
            {profile.supplier_type}
          </span>
        </div>
        {profile.oc_number && (
          <span className="inline-flex items-center gap-1.5 bg-purple-400/[.08] text-purple-400 text-[11px] font-medium px-2.5 py-1.5 rounded-md border border-purple-400/15 font-['IBM_Plex_Mono']">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/>
            </svg>
            {profile.oc_number}
          </span>
        )}
      </div>

      {/* Data rows */}
      <div className="px-4 mb-6">
        {[
          ['Company', profile.supplier_type === 'INFLUENCER' ? 'DAZZLE MGMT' : 'All'],
          ['NIF/CIF', profile.nif_cif, true],
          ['Email', profile.email, false, true],
          ['Phone', profile.phone],
          ['Address', profile.address],
          ['IBAN', profile.iban_masked, true],
          ['Bank cert', null, false, false, true],
          ['Member since', profile.created_at ? new Date(profile.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—', true],
        ].map(([label, value, mono, amber, isPdf]) => (
          <div key={label} className="flex justify-between items-center py-2 border-b border-white/[.04] last:border-0 text-[13px]">
            <span className="text-zinc-500">{label}</span>
            {isPdf ? (
              <span className="text-red-400 text-xs cursor-pointer flex items-center gap-1">
                View PDF <ExternalLink size={10} />
              </span>
            ) : (
              <span className={`text-right max-w-[200px] break-all ${
                mono ? "font-['IBM_Plex_Mono'] text-xs" : 'text-sm'
              } ${amber ? 'text-amber-400' : 'text-zinc-200'}`}>
                {value || '—'}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Profile;
