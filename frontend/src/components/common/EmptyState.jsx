const EmptyState = ({ icon = null, message, subtitle = null, action = null }) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-12 text-center">
    {icon && <div className="mx-auto mb-4 text-zinc-600">{icon}</div>}
    <p className="text-zinc-400 mb-2">{message}</p>
    {subtitle && <p className="text-sm text-zinc-600">{subtitle}</p>}
    {action && (
      <button onClick={action.onClick} className="text-amber-500 hover:text-amber-400 text-sm mt-2">
        {action.label}
      </button>
    )}
  </div>
);

export default EmptyState;
