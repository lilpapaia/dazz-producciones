import { memo } from 'react';

const StatCard = memo(({ icon: Icon, secondaryIcon: SecondaryIcon, badge, iconColor, label, value, valueColor, subtitle }) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 hover:border-amber-500 transition-colors">
    <div className="flex items-center justify-between mb-4">
      <Icon size={32} className={iconColor} />
      {SecondaryIcon && <SecondaryIcon size={20} className="text-green-400" />}
      {badge && (
        <div className="bg-green-500/20 px-2 py-1 rounded text-xs font-bold text-green-400">{badge}</div>
      )}
    </div>
    <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">{label}</p>
    <p className={`text-3xl font-bold ${valueColor} mb-1`}>{value}</p>
    <p className="text-xs text-zinc-400">{subtitle}</p>
  </div>
));

StatCard.displayName = 'StatCard';

export default StatCard;
