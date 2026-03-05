import { AlertTriangle, X } from 'lucide-react';

const ConfirmDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  type = "danger" // danger | warning | info
}) => {
  if (!isOpen) return null;

  const colors = {
    danger: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      text: 'text-red-400',
      button: 'bg-red-500 hover:bg-red-600',
      icon: 'text-red-400'
    },
    warning: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      text: 'text-amber-400',
      button: 'bg-amber-500 hover:bg-amber-600',
      icon: 'text-amber-400'
    },
    info: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      button: 'bg-blue-500 hover:bg-blue-600',
      icon: 'text-blue-400'
    }
  };

  const theme = colors[type];

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="bg-zinc-900 border border-zinc-800 rounded-sm max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className={`${theme.bg} ${theme.border} border p-2 rounded-sm`}>
              <AlertTriangle className={theme.icon} size={24} />
            </div>
            <h3 className="text-lg font-bold text-zinc-100">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-100 transition-colors p-1"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <p className="text-zinc-300 text-sm leading-relaxed">{message}</p>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-zinc-800">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
          >
            {cancelText}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`flex-1 px-4 py-2.5 ${theme.button} text-white rounded-sm transition-colors font-bold shadow-lg`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
