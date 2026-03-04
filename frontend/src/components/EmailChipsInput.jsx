import { useState } from 'react';
import { X } from 'lucide-react';

const EmailChipsInput = ({ emails, onChange, label }) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',' || e.key === ' ') {
      e.preventDefault();
      addEmail();
    } else if (e.key === 'Backspace' && inputValue === '' && emails.length > 0) {
      // Si presiona backspace con input vacío, elimina último email
      removeEmail(emails.length - 1);
    }
  };

  const addEmail = () => {
    const trimmedEmail = inputValue.trim().replace(/,$/g, ''); // Quitar coma final
    
    if (!trimmedEmail) return;

    if (!validateEmail(trimmedEmail)) {
      setError('Email inválido');
      return;
    }

    if (emails.includes(trimmedEmail)) {
      setError('Este email ya está en la lista');
      return;
    }

    onChange([...emails, trimmedEmail]);
    setInputValue('');
    setError('');
  };

  const removeEmail = (index) => {
    onChange(emails.filter((_, i) => i !== index));
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedText = e.clipboardData.getData('text');
    const emailList = pastedText
      .split(/[\s,;]+/)
      .map(email => email.trim())
      .filter(email => email && validateEmail(email));
    
    const newEmails = [...emails, ...emailList.filter(email => !emails.includes(email))];
    onChange(newEmails);
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm text-zinc-400 font-medium">{label}</label>
      )}
      
      <div className="min-h-[80px] p-3 bg-zinc-900 border border-zinc-700 rounded-sm focus-within:border-amber-500 transition-colors">
        {/* Chips de emails */}
        <div className="flex flex-wrap gap-2 mb-2">
          {emails.map((email, index) => (
            <div
              key={index}
              className="group flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/20 border border-amber-500/30 text-amber-400 rounded-full text-sm font-medium hover:bg-amber-500/30 transition-colors"
            >
              <span>{email}</span>
              <button
                onClick={() => removeEmail(index)}
                className="hover:bg-amber-500/40 rounded-full p-0.5 transition-colors"
                type="button"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>

        {/* Input para nuevo email */}
        <input
          type="email"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setError('');
          }}
          onKeyDown={handleKeyDown}
          onBlur={addEmail}
          onPaste={handlePaste}
          placeholder={emails.length === 0 ? "Escribe un email y presiona Enter..." : "Añadir otro email..."}
          className="w-full bg-transparent text-zinc-100 text-sm placeholder:text-zinc-600 focus:outline-none"
        />
      </div>

      {/* Error message */}
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <span>⚠️</span> {error}
        </p>
      )}

      {/* Hints */}
      <p className="text-xs text-zinc-600">
        💡 Presiona Enter, coma o espacio para añadir • Backspace para eliminar
      </p>
    </div>
  );
};

export default EmailChipsInput;
