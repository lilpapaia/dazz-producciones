import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach supplier JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('supplier_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto refresh on 401
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(p => error ? p.reject(error) : p.resolve(token));
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/portal/refresh') &&
      !original.url?.includes('/portal/login')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }
      original._retry = true;
      isRefreshing = true;
      const refreshToken = localStorage.getItem('supplier_refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('supplier_token');
        localStorage.removeItem('supplier_refresh_token');
        localStorage.removeItem('supplier_data');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      try {
        const { data } = await axios.post(`${API_URL}/portal/refresh`, { refresh_token: refreshToken });
        localStorage.setItem('supplier_token', data.access_token);
        processQueue(null, data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        processQueue(error);
        localStorage.removeItem('supplier_token');
        localStorage.removeItem('supplier_refresh_token');
        localStorage.removeItem('supplier_data');
        window.location.href = '/login';
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const validateToken = (token) => api.get(`/portal/register/validate/${token}`);
export const checkOcForRegistration = (nif, name, token) =>
  api.get('/portal/register/check-oc', { params: { nif: nif || undefined, name: name || undefined, token } });
export const registerSupplier = (data) => api.post('/portal/register', data);
export const loginSupplier = (data) => api.post('/portal/login', data);
export const logoutSupplier = (refreshToken) => api.post('/portal/logout', { refresh_token: refreshToken });

// Profile
export const getProfile = () => api.get('/portal/profile');
export const uploadBankCert = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/portal/bank-cert', form, { headers: { 'Content-Type': 'multipart/form-data' } });
};

export const getBankCertUrl = () => api.get('/portal/bank-cert-url');
export const validateBankCertIban = (iban, file, nifCif, token) => {
  const form = new FormData();
  form.append('file', file);
  let url = `/portal/validate-bank-cert?iban=${encodeURIComponent(iban)}&token=${encodeURIComponent(token)}`;
  if (nifCif) url += `&nif_cif=${encodeURIComponent(nifCif)}`;
  return api.post(url, form, { headers: { 'Content-Type': 'multipart/form-data' } });
};

// Invoices
export const uploadInvoice = (file, options = {}) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/portal/invoices/upload', form, { headers: { 'Content-Type': 'multipart/form-data' }, signal: options.signal });
};
export const getMyInvoices = (params) => api.get('/portal/invoices', { params });
export const getReceivedInvoices = (params) => api.get('/portal/invoices/received', { params });
export const requestDeleteInvoice = (id, reason) => api.delete(`/portal/invoices/${id}`, { data: { reason } });

// Summary
export const getSummary = () => api.get('/portal/summary');

// Notifications
export const getNotifications = (params) => api.get('/portal/notifications', { params });
export const markNotificationRead = (id) => api.put(`/portal/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.put('/portal/notifications/read-all');

// Account actions
export const requestDataChange = (data) => api.post('/portal/request-data-change', data);
export const requestIbanChange = (newIban, file) => {
  const form = new FormData();
  form.append('file', file);
  form.append('new_iban', newIban);
  return api.post('/portal/request-iban-change', form, { headers: { 'Content-Type': 'multipart/form-data' } });
};
export const requestDeactivation = (data) => api.post('/portal/request-deactivation', data);

export default api;
