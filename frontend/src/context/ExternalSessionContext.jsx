import { createContext, useState, useContext, useMemo, useCallback } from 'react';

/**
 * Sesión del acceso externo (FEAT-09). Patrón análogo a AuthContext pero:
 * - Guarda el JWT guest en sessionStorage (se pierde al cerrar la pestaña → más seguro
 *   que localStorage para un acceso temporal por link + PIN).
 * - NO decodifica el JWT para validar expiración: el backend revalida is_active /
 *   expires_at / locked_until en cada request.
 */

const ExternalSessionContext = createContext();

// Claves en sessionStorage
const K_TOKEN = 'guest_token';
const K_NAME = 'guest_name';
const K_PROJECT = 'guest_project_id';
const K_SHARE = 'guest_share_token'; // token de la URL (/share/:token) — para volver al PIN tras 401

export const ExternalSessionProvider = ({ children }) => {
  // Inicialización síncrona desde sessionStorage → sin flash: el primer render ya
  // refleja si hay sesión (evita que ExternalRoute redirija con sesión válida).
  const [session, setSession] = useState(() => ({
    token: sessionStorage.getItem(K_TOKEN),
    guestName: sessionStorage.getItem(K_NAME),
    projectId: sessionStorage.getItem(K_PROJECT),
  }));

  const loginGuest = useCallback((accessToken, guestName, projectId, shareToken) => {
    sessionStorage.setItem(K_TOKEN, accessToken);
    sessionStorage.setItem(K_NAME, guestName ?? '');
    sessionStorage.setItem(K_PROJECT, projectId != null ? String(projectId) : '');
    if (shareToken) sessionStorage.setItem(K_SHARE, shareToken);
    setSession({ token: accessToken, guestName, projectId });
  }, []);

  const logoutGuest = useCallback(() => {
    sessionStorage.removeItem(K_TOKEN);
    sessionStorage.removeItem(K_NAME);
    sessionStorage.removeItem(K_PROJECT);
    // guest_share_token se conserva: permite volver a la pantalla de PIN.
    setSession({ token: null, guestName: null, projectId: null });
  }, []);

  const value = useMemo(() => ({
    token: session.token,
    guestName: session.guestName,
    projectId: session.projectId,
    isAuthenticated: !!session.token,
    loginGuest,
    logoutGuest,
  }), [session, loginGuest, logoutGuest]);

  return (
    <ExternalSessionContext.Provider value={value}>
      {children}
    </ExternalSessionContext.Provider>
  );
};

export const useExternalSession = () => {
  const context = useContext(ExternalSessionContext);
  if (!context) {
    throw new Error('useExternalSession must be used within ExternalSessionProvider');
  }
  return context;
};
