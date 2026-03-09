import { useState, useEffect, useRef } from 'react';
import { getUsernames } from '../services/api';
import { User, ChevronDown } from 'lucide-react';

/**
 * Componente de autocompletado para seleccionar un usuario registrado
 * Props:
 *   - value: nombre del usuario seleccionado
 *   - onChange: callback cuando se selecciona un usuario (recibe el nombre)
 *   - label: etiqueta del campo
 *   - required: si es obligatorio
 */
const UserAutocomplete = ({ value, onChange, label = "RESPONSABLE", required = false }) => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [inputValue, setInputValue] = useState(value || '');
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(true);
  const wrapperRef = useRef(null);

  // Cargar usuarios al montar
  useEffect(() => {
    loadUsers();
  }, []);

  // Sincronizar valor externo
  useEffect(() => {
    setInputValue(value || '');
  }, [value]);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUsers = async () => {
    try {
      const response = await getUsernames();
      setUsers(response.data);
      setFilteredUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInputValue(val);
    setShowDropdown(true);

    // Filtrar usuarios
    if (val.trim()) {
      const filtered = users.filter(user =>
        user.name.toLowerCase().includes(val.toLowerCase()) ||
        user.email.toLowerCase().includes(val.toLowerCase())
      );
      setFilteredUsers(filtered);
    } else {
      setFilteredUsers(users);
    }

    // Si el valor coincide exactamente con un usuario, seleccionarlo
    const exactMatch = users.find(u => u.name.toLowerCase() === val.toLowerCase());
    if (exactMatch) {
      onChange(exactMatch.name);
    } else {
      onChange(val); // Permite texto libre si no hay match
    }
  };

  const handleSelectUser = (user) => {
    setInputValue(user.name);
    onChange(user.name);
    setShowDropdown(false);
  };

  const handleFocus = () => {
    setShowDropdown(true);
    setFilteredUsers(users);
  };

  return (
    <div className="relative" ref={wrapperRef}>
      <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">
        {label} {required && '*'}
      </label>
      
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
          <User size={18} />
        </div>
        
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          placeholder={loading ? "Cargando usuarios..." : "Escribe para buscar..."}
          className="w-full bg-zinc-950 border border-zinc-700 rounded-sm pl-10 pr-10 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
          required={required}
          disabled={loading}
        />
        
        <button
          type="button"
          onClick={() => setShowDropdown(!showDropdown)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-zinc-500 hover:text-zinc-300"
        >
          <ChevronDown size={18} className={`transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Dropdown de usuarios */}
      {showDropdown && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-700 rounded-sm shadow-xl max-h-60 overflow-y-auto">
          {filteredUsers.length === 0 ? (
            <div className="px-4 py-3 text-zinc-500 text-sm text-center">
              No se encontraron usuarios
            </div>
          ) : (
            filteredUsers.map((user) => (
              <div
                key={user.id}
                onClick={() => handleSelectUser(user)}
                className={`px-4 py-3 cursor-pointer transition-colors hover:bg-zinc-800 border-b border-zinc-800 last:border-0 ${
                  inputValue === user.name ? 'bg-amber-500/10 border-l-2 border-l-amber-500' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm">
                    {user.role === 'admin' ? '👑' : '👤'}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-zinc-100">{user.name}</p>
                    <p className="text-xs text-zinc-500">{user.email}</p>
                  </div>
                  {inputValue === user.name && (
                    <span className="text-amber-500 text-xs">✓ Seleccionado</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Helper text */}
      <p className="text-xs text-zinc-500 mt-1">
        Selecciona un usuario registrado en el sistema
      </p>
    </div>
  );
};

export default UserAutocomplete;
