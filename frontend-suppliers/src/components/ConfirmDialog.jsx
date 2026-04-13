import { AlertTriangle, X } from 'lucide-react';

const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  type = "danger"
}) => {
  if (!isOpen) return null;

  const colors = {
    danger: {
      bg: 'bg-red-500/10', border: 'border-red-500/30',
      button: 'bg-red-500 hover:bg-red-600', icon: 'text-red-400'
    },
    warning: {
      bg: 'bg-amber-500/10', border: 'border-amber-500/30',
      button: 'bg-amber-500 hover:bg-amber-600', icon: 'text-amber-400'
    },
  };

  const theme = colors[type] || colors.danger;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className={`${theme.bg} ${theme.border} border p-2 rounded-lg`}>
              <AlertTriangle className={theme.icon} size={20} />
            </div>
            <h3 className="text-base font-bold text-zinc-100">{title}</h3>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-zinc-100 transition-colors p-1">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">
          <p className="text-zinc-300 text-sm leading-relaxed">{message}</p>
        </div>
        <div className="flex gap-3 p-5 border-t border-zinc-800">
          <button onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors font-semibold text-sm">
            {cancelText}
          </button>
          <button onClick={() => { onConfirm(); onClose(); }}
            className={`flex-1 px-4 py-2.5 ${theme.button} text-white rounded-lg transition-colors font-bold text-sm shadow-lg`}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
