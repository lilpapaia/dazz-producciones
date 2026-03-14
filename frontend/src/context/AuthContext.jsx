import { createContext, useState, useContext, useEffect } from 'react';
import { logoutApi } from '../services/api';

const AuthContext = createContext();

// VULN-019: Solo guardar campos mínimos necesarios del usuario
const sanitizeUserData = (userData) => {
  if (!userData) return null;
  return {
    id: userData.id,
    name: userData.name,
    email: userData.email,
    role: userData.role,
  };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
    }

    setLoading(false);
  }, []);

  const login = (token, refreshToken, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refresh_token', refreshToken);
    // VULN-019: Solo guardar campos mínimos
    const safeUserData = sanitizeUserData(userData);
    localStorage.setItem('user', JSON.stringify(safeUserData));
    setUser(safeUserData);
  };

  const logout = async () => {
    // VULN-009: Revocar refresh token en el servidor
    try {
      await logoutApi();
    } catch (error) {
      // Ignorar errores de logout (token puede estar ya expirado)
      console.error('Error during logout:', error);
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updateUser = (userData) => {
    const safeUserData = sanitizeUserData(userData);
    localStorage.setItem('user', JSON.stringify(safeUserData));
    setUser(safeUserData);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
