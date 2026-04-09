import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { logoutSupplier } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [supplier, setSupplier] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('supplier_token');
    const stored = localStorage.getItem('supplier_data');
    if (token && stored) {
      try { setSupplier(JSON.parse(stored)); } catch { /* ignore */ }
    }
    setLoading(false);
  }, []);

  const login = useCallback((data) => {
    localStorage.setItem('supplier_token', data.access_token);
    localStorage.setItem('supplier_refresh_token', data.refresh_token);
    localStorage.setItem('supplier_data', JSON.stringify(data.supplier));
    setSupplier(data.supplier);
  }, []);

  const logout = useCallback(async () => {
    const rt = localStorage.getItem('supplier_refresh_token');
    if (rt) { try { await logoutSupplier(rt); } catch { /* ignore */ } }
    localStorage.removeItem('supplier_token');
    localStorage.removeItem('supplier_refresh_token');
    localStorage.removeItem('supplier_data');
    setSupplier(null);
  }, []);

  const value = useMemo(() => ({ supplier, login, logout, loading }), [supplier, login, logout, loading]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
