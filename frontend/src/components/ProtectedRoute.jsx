import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * NOTA DE SEGURIDAD: Esta protección de rutas es SOLO visual/UX.
 * La seguridad real de permisos está implementada en el backend
 * (FastAPI con JWT + verificación de roles en cada endpoint).
 * Un usuario podría manipular localStorage para ver la UI de admin,
 * pero no podría ejecutar ninguna acción sin un token JWT válido
 * con los permisos correctos.
 */
const ProtectedRoute = ({ children, adminOnly = false, adminOrBossOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Solo ADMIN
  if (adminOnly && user.role !== 'ADMIN') {
    return <Navigate to="/dashboard" replace />;
  }

  // ADMIN o BOSS (para Statistics)
  if (adminOrBossOnly && user.role !== 'ADMIN' && user.role !== 'BOSS') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default ProtectedRoute;
