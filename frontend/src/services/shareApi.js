import axios from 'axios';

/**
 * Instancia axios para el acceso externo (FEAT-09). Aislada de api.js:
 * - Adjunta el JWT guest desde sessionStorage (no localStorage).
 * - En 401 NO va a /login (eso es de empleados): limpia la sesión y vuelve a la
 *   pantalla de PIN. NO intenta refresh (el guest no tiene refresh token).
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const shareApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

shareApi.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('guest_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

shareApi.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || '';
    // NO interceptar el propio validate-pin: un PIN incorrecto devuelve 401 y debe
    // mostrarlo la pantalla de PIN, no limpiar la sesión ni redirigir.
    if (error.response?.status === 401 && !url.includes('/guest/validate-pin')) {
      sessionStorage.removeItem('guest_token');
      sessionStorage.removeItem('guest_name');
      sessionStorage.removeItem('guest_project_id');
      const shareToken = sessionStorage.getItem('guest_share_token');
      if (shareToken) {
        window.location.href = `/share/${shareToken}`;
      }
    }
    return Promise.reject(error);
  }
);

export default shareApi;

// ============================================
// GUEST API
// ============================================

export const validatePin = (token, pin) =>
  shareApi.post('/guest/validate-pin', { token, pin });

export const getGuestProject = () => shareApi.get('/guest/project');

export const getGuestTickets = () => shareApi.get('/guest/tickets');

export const uploadGuestTicket = (formData, options = {}) =>
  shareApi.post('/guest/tickets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal: options.signal,
  });

export const updateGuestTicket = (ticketId, data) =>
  shareApi.put(`/guest/tickets/${ticketId}`, data);

export const deleteGuestTicket = (ticketId) =>
  shareApi.delete(`/guest/tickets/${ticketId}`);

// El "suplido" del externo se guarda en el PUT (updateGuestTicket incluye is_suplido).

export const downloadGuestExcel = () =>
  shareApi.get('/guest/project/excel', { responseType: 'blob' });
