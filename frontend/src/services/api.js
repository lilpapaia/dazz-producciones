import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// VULN-009: Interceptor con refresh token automático
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Solo interceptar 401 (token expirado/inválido) — NO 403 (permisos insuficientes)
    // 403 de permisos (non-admin en endpoint admin) debe propagarse como error normal
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      if (isRefreshing) {
        // Si ya estamos refrescando, encolar la petición
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (!refreshToken) {
        // Sin refresh token, limpiar y redirigir
        isRefreshing = false;
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });

        const newAccessToken = response.data.access_token;
        localStorage.setItem('token', newAccessToken);

        // Reintentar peticiones encoladas
        processQueue(null, newAccessToken);

        // Reintentar la petición original
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token inválido — logout completo
        processQueue(refreshError, null);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ============================================
// AUTH
// ============================================

export const login = (identifier, password) =>
  api.post('/auth/login', { identifier, password });

export const registerUser = (data) =>
  api.post('/auth/register', data);

export const setPassword = (token, newPassword) =>
  api.post('/auth/set-password', { token, new_password: newPassword });

export const forgotPassword = (email) =>
  api.post('/auth/forgot-password', { email });

// VULN-009: Logout con revocación de refresh token
export const logoutApi = () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (refreshToken) {
    return api.post('/auth/logout', { refresh_token: refreshToken });
  }
  return Promise.resolve();
};

// ============================================
// PROJECTS
// ============================================

export const getProjects = () => api.get('/projects');

export const getProject = (id) => api.get(`/projects/${id}`);

export const createProject = (data) => api.post('/projects', data);

export const updateProject = (id, data) => api.put(`/projects/${id}`, data);

export const closeProject = (id) => api.post(`/projects/${id}/close`);

export const reopenProject = (id) => api.post(`/projects/${id}/reopen`);

export const closeProjectWithDownload = (id) =>
  api.post(`/projects/${id}/close`, {}, {
    responseType: 'blob'
  });

export const closeProjectWithEmails = (id, emails) =>
  api.post(`/projects/${id}/close`,
    { recipients: emails },
    { responseType: 'blob' }
  );

export const deleteProject = (id) => api.delete(`/projects/${id}`);

// ============================================
// TICKETS
// ============================================

export const uploadTicket = (projectId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/tickets/${projectId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const getProjectTickets = (projectId) =>
  api.get(`/tickets/${projectId}/tickets`);

export const getTicket = (id) =>
  api.get(`/tickets/${id}`);

export const updateTicket = (id, data) =>
  api.put(`/tickets/${id}`, data);

export const deleteTicket = (id) =>
  api.delete(`/tickets/${id}`);

// ============================================
// USERS
// ============================================

export const getUsers = () => api.get('/users');

export const getUsernames = (params) => api.get('/users/usernames', { params });

export const getUser = (id) => api.get(`/users/${id}`);

export const updateUser = (id, data) => api.put(`/users/${id}`, data);

export const deleteUser = (id) => api.delete(`/users/${id}`);

// ============================================
// ESTADÍSTICAS
// ============================================

export const getAvailableYears = () => api.get('/statistics/available-years');

export const getStatisticsOverview = (year, quarter = null, geoFilter = null) => {
  const params = { year };
  if (quarter) params.quarter = quarter;
  if (geoFilter) params.geo_filter = geoFilter;
  return api.get('/statistics/overview', { params });
};

export const getMonthlyEvolution = (year) =>
  api.get('/statistics/monthly-evolution', { params: { year } });

export const getCurrencyDistribution = (year, quarter = null) => {
  const params = { year };
  if (quarter) params.quarter = quarter;
  return api.get('/statistics/currency-distribution', { params });
};

export const getForeignBreakdown = (year, quarter = null) => {
  const params = { year };
  if (quarter) params.quarter = quarter;
  return api.get('/statistics/foreign-breakdown', { params });
};

export const getCompleteStatistics = (year, quarter = null, geoFilter = null, companyId = null) => {
  const params = { year };
  if (quarter) params.quarter = quarter;
  if (geoFilter) params.geo_filter = geoFilter;
  if (companyId) params.company_id = companyId;
  return api.get('/statistics/complete', { params });
};

// ============================================
// COMPANIES
// ============================================

export const getCompanies = () => api.get('/companies');
