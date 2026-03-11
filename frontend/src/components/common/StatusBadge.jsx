const BADGE_CONFIG = {
  project: {
    en_curso: { classes: 'bg-green-500/20 text-green-400 border-green-500/30', label: 'EN CURSO' },
    cerrado: { classes: 'bg-gray-100 text-gray-800 border-gray-300', label: 'CERRADO' },
  },
  ticket: {
    factura: { classes: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'FACTURA' },
    ticket: { classes: 'bg-zinc-700/50 text-zinc-400 border-zinc-600', label: 'TICKET' },
  },
  role: {
    ADMIN: { classes: 'bg-amber-500/20 text-amber-400 border-amber-500/30', label: 'ADMIN' },
    BOSS: { classes: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'BOSS' },
    WORKER: { classes: 'bg-zinc-700/50 text-zinc-400 border-zinc-600', label: 'WORKER' },
  },
  payment: {
    paid: { classes: 'bg-green-500/20 text-green-400' },
    unpaid: { classes: 'bg-red-500/20 text-red-400' },
  },
  geo: {
    UE: { classes: 'bg-blue-500/20 text-blue-400' },
    INTERNACIONAL: { classes: 'bg-purple-500/20 text-purple-400' },
  },
};

const StatusBadge = ({ type, value, className = '' }) => {
  const config = BADGE_CONFIG[type]?.[value];
  if (!config) return null;
  const label = config.label || value;
  return (
    <span className={`px-2 py-1 text-xs font-mono tracking-wider rounded-sm border whitespace-nowrap ${config.classes} ${className}`}>
      {label}
    </span>
  );
};

export default StatusBadge;
