import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, getBankCertUrl } from '../services/api';
import { ExternalLink, Edit3, CreditCard, UserMinus, Info, X, Download, FileText } from 'lucide-react';
import useEscapeKey from '../hooks/useEscapeKey';

const STATUS_MAP = {
  ACTIVE: { cls: 'bg-green-400/10 text-green-400 border-green-400/20', label: 'ACTIVE' },
  NEW: { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', label: 'NEW' },
  DEACTIVATED: { cls: 'bg-zinc-700/50 text-zinc-500 border-zinc-700', label: 'DEACTIVATED' },
};

const Profile = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [certError, setCertError] = useState('');
  const [certUrl, setCertUrl] = useState(null);
  const [showCertLightbox, setShowCertLightbox] = useState(false);

  useEffect(() => {
    getProfile().then(r => setProfile(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEscapeKey(() => setShowCertLightbox(false), showCertLightbox);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const handleViewCert = async () => {
    try {
      const { data } = await getBankCertUrl();
      setCertUrl(data.url);
      setShowCertLightbox(true);
    } catch { setCertError('Could not load bank certificate'); }
  };

  if (!profile) return null;

  const initials = profile.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div className="max-w-2xl lg:max-w-4xl mx-auto pt-4 lg:pt-6">
      {/* Desktop: 2-column grid / Mobile: single column */}
      <div className="lg:grid lg:grid-cols-[320px_1fr] lg:gap-5 px-4 lg:px-6">

        {/* ═══ LEFT: Profile data ═══ */}
        <div>
          <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 lg:p-5 mb-3">
            {/* Avatar + name */}
            <div className="flex items-center gap-2.5 lg:gap-3 mb-3 lg:mb-4">
              <div className="w-12 h-12 lg:w-16 lg:h-16 bg-amber-500 rounded-[10px] flex items-center justify-center font-['Bebas_Neue'] text-[20px] lg:text-[26px] text-zinc-950 flex-shrink-0">
                {initials}
              </div>
              <div>
                <div className="font-['Bebas_Neue'] text-[18px] lg:text-[22px] tracking-wide text-zinc-100 leading-tight">
                  {profile.name?.toUpperCase()}
                </div>
                <div className="mt-1">
                  <span className={`text-[10px] font-bold px-[7px] py-[1px] rounded border ${(STATUS_MAP[profile.status] || STATUS_MAP.ACTIVE).cls}`}>
                    {(STATUS_MAP[profile.status] || STATUS_MAP.ACTIVE).label}
                  </span>
                </div>
              </div>
            </div>

            {/* OC badge */}
            {profile.oc_number && (
              <div className="mb-3">
                <span className="inline-flex items-center gap-1.5 bg-purple-400/[.08] text-purple-400 text-[11px] font-medium px-2.5 py-1.5 rounded-md border border-purple-400/15 font-['IBM_Plex_Mono']">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/>
                  </svg>
                  {profile.oc_number}
                </span>
              </div>
            )}

            <hr className="border-white/[.04] mb-2" />

            {/* Data rows */}
            {[
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
                  <div>
                    <button onClick={() => { setCertError(''); handleViewCert(); }} className="text-red-400 text-xs cursor-pointer flex items-center gap-1 hover:text-red-300 transition-colors">
                      View PDF <ExternalLink size={10} />
                    </button>
                    {certError && <span className="text-red-400 text-[10px]">{certError}</span>}
                  </div>
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

          {/* Legal documents */}
          {(profile.privacy_accepted_at || profile.contract_accepted_at) && (
            <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 lg:p-5 mb-3">
              <div className="text-[10px] font-semibold text-zinc-500 tracking-widest uppercase mb-2.5">Legal documents</div>
              <div className="space-y-2">
                {profile.privacy_accepted_at && (
                  <div className="flex items-center justify-between py-1.5">
                    <div className="flex items-center gap-2">
                      <FileText size={13} className="text-zinc-500" />
                      <div>
                        <div className="text-[13px] text-zinc-300">Privacy Policy</div>
                        <div className="text-[10px] text-zinc-600">Accepted on {new Date(profile.privacy_accepted_at).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}</div>
                      </div>
                    </div>
                    <a href="/docs/privacy-policy.pdf" download className="inline-flex items-center gap-1 border border-zinc-700 text-zinc-400 text-[11px] px-2.5 py-1 rounded hover:bg-zinc-800 transition-colors">
                      <Download size={10} /> PDF
                    </a>
                  </div>
                )}
                {profile.contract_accepted_at && (
                  <div className="flex items-center justify-between py-1.5">
                    <div className="flex items-center gap-2">
                      <FileText size={13} className="text-zinc-500" />
                      <div>
                        <div className="text-[13px] text-zinc-300">Agency Contract</div>
                        <div className="text-[10px] text-zinc-600">Accepted on {new Date(profile.contract_accepted_at).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}</div>
                      </div>
                    </div>
                    <a href="/docs/agency-contract.pdf" download className="inline-flex items-center gap-1 border border-zinc-700 text-zinc-400 text-[11px] px-2.5 py-1 rounded hover:bg-zinc-800 transition-colors">
                      <Download size={10} /> PDF
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ═══ RIGHT: Actions ═══ */}
        <div>
          {/* Pending change card */}
          {profile.has_pending_change && (
            <div className="bg-amber-500/[.04] border border-amber-500/15 rounded-[10px] p-3 mb-3">
              <div className="flex items-center mb-1">
                <span className="w-[6px] h-[6px] bg-amber-500 rounded-full animate-pulse mr-1.5" />
                <span className="text-[12px] font-semibold text-amber-400">Pending change request</span>
              </div>
              <div className="text-[12px] text-zinc-400">
                {profile.pending_change_info || 'A change request is awaiting admin approval. Your current data remains active.'}
              </div>
            </div>
          )}

          {/* Account actions */}
          <div className="bg-[#18181b] border border-zinc-800 rounded-[10px] p-3.5 lg:p-5 mb-3">
            <div className="text-[11px] font-semibold text-zinc-400 tracking-widest uppercase mb-3">Account actions</div>
            <div className="flex flex-col gap-[7px]">
              <button onClick={() => navigate('/profile/edit-data')}
                className="w-full text-left bg-zinc-800 border border-zinc-700 rounded-lg px-3.5 py-2.5 lg:py-3 text-[13px] text-zinc-300 hover:bg-zinc-700 transition-colors flex items-center gap-2">
                <Edit3 size={13} strokeWidth={1.5} /> Edit my data
              </button>
              <button onClick={() => navigate('/profile/change-iban')}
                className="w-full text-left bg-zinc-800 border border-zinc-700 rounded-lg px-3.5 py-2.5 lg:py-3 text-[13px] text-zinc-300 hover:bg-zinc-700 transition-colors flex items-center gap-2">
                <CreditCard size={13} strokeWidth={1.5} /> Change IBAN & bank certificate
              </button>
              <button onClick={() => navigate('/profile/deactivation')}
                className="w-full text-left bg-red-400/10 border border-red-400/25 rounded-lg px-3.5 py-2.5 lg:py-3 text-[13px] text-red-400 hover:bg-red-400/20 transition-colors flex items-center gap-2">
                <UserMinus size={13} strokeWidth={1.5} /> Request account deactivation
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="bg-blue-400/[.06] text-blue-400 border border-blue-400/[.12] rounded-lg p-2.5 text-[11px] flex items-start gap-2 leading-relaxed">
            <Info size={13} className="flex-shrink-0 mt-0.5" strokeWidth={1.5} />
            Email cannot be changed — it is your account identifier. For assistance contact admin@dazzcreative.com
          </div>
        </div>
      </div>

      {/* ═══ LIGHTBOX: Certificado bancario PDF ═══ */}
      {showCertLightbox && certUrl && (
        <div className="fixed inset-0 bg-black z-50 flex flex-col"
          style={{ minHeight: '100dvh', paddingTop: 'env(safe-area-inset-top, 0px)', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
            <span className="text-[13px] text-zinc-400">Bank certificate</span>
            <div className="flex items-center gap-2">
              <a href={certUrl} target="_blank" rel="noopener noreferrer"
                className="text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700">
                <Download size={18} /></a>
              <button onClick={() => setShowCertLightbox(false)}
                className="text-white hover:text-amber-500 transition-colors bg-zinc-900/80 rounded-full p-2 border border-zinc-700">
                <X size={18} /></button>
            </div>
          </div>
          <div className="flex-1 min-h-0 flex items-center justify-center bg-zinc-950">
            {certUrl && (certUrl.includes('/image/upload/') || /\.(jpg|jpeg|png|webp)$/i.test(certUrl)) ? (
              <img src={certUrl} alt="Bank certificate" className="max-w-full max-h-full object-contain" />
            ) : (
              <iframe src={certUrl} className="w-full h-full bg-white" title="Bank certificate" />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
