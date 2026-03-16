import { useState, useEffect } from 'react';
import { getProfile } from '../services/api';
import { Mail } from 'lucide-react';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile()
      .then(r => setProfile(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!profile) return null;

  const initials = profile.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  const rows = [
    ['Email', profile.email],
    ['NIF/CIF', profile.nif_cif || 'Not set'],
    ['Phone', profile.phone || 'Not set'],
    ['Address', profile.address || 'Not set'],
    ['IBAN', profile.iban_masked || 'Not set'],
    ['Type', profile.supplier_type],
  ];

  if (profile.oc_number) {
    rows.push(['OC', profile.oc_number]);
  }

  return (
    <div className="px-4 pt-4 max-w-lg mx-auto">
      <h1 className="font-['Bebas_Neue'] text-xl tracking-wider text-zinc-100 mb-4">My profile</h1>

      {/* Banner: contact admin to change data */}
      <div className="bg-amber-500/[.06] text-amber-400 border border-amber-500/[.12] rounded-xl p-3 text-xs mb-4 flex items-start gap-2">
        <Mail size={14} className="flex-shrink-0 mt-0.5" />
        <span>To update your details, please contact the DAZZ admin team at <strong>admin@dazzcreative.com</strong></span>
      </div>

      {/* Profile card */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center font-['Bebas_Neue'] text-lg text-zinc-950">{initials}</div>
          <div>
            <div className="font-['Bebas_Neue'] text-base tracking-wide text-zinc-100">{profile.name}</div>
            <div className="text-[11px] text-zinc-500">Member since {new Date(profile.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</div>
          </div>
        </div>

        <div className="space-y-1.5">
          {rows.map(([label, value]) => (
            <div key={label} className="bg-zinc-800 rounded-md p-2.5 border border-zinc-700">
              <div className="text-[9px] text-zinc-500 tracking-widest uppercase mb-0.5">{label}</div>
              <div className="text-xs font-medium text-zinc-200 font-mono">{value}</div>
            </div>
          ))}
        </div>

        {profile.oc_number && (
          <div className="mt-3 inline-flex items-center gap-1.5 bg-purple-400/[.08] text-purple-400 text-[11px] font-medium px-2.5 py-1.5 rounded border border-purple-400/15 font-mono">
            {profile.oc_number}
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
