import { Navigate, useParams } from 'react-router-dom';
import { useExternalSession } from '../context/ExternalSessionContext';

/**
 * Guard de rutas externas (FEAT-09). Equivalente a ProtectedRoute pero para el guest:
 * sin sesión válida → redirige a la pantalla de PIN (/share/:token).
 *
 * NOTA DE SEGURIDAD: esto es solo UX. La seguridad real está en el backend, que
 * exige el JWT guest (type=guest) y revalida el token en cada request.
 */
const ExternalRoute = ({ children }) => {
  const { isAuthenticated } = useExternalSession();
  const { token } = useParams();

  if (!isAuthenticated) {
    const target = token || sessionStorage.getItem('guest_share_token');
    return <Navigate to={`/share/${target || ''}`} replace />;
  }

  return children;
};

export default ExternalRoute;
