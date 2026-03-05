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

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ============================================
// AUTH
// ============================================

export const login = (email, password) =>
  api.post('/auth/login', { email, password });

export const registerUser = (data) =>
  api.post('/auth/register', data);

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

export const getUser = (id) => api.get(`/users/${id}`);

export const updateUser = (id, data) => api.put(`/users/${id}`, data);

export const deleteUser = (id) => api.delete(`/users/${id}`);

// ============================================
// ESTADÍSTICAS
// ============================================

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

export const getCompleteStatistics = (year, quarter = null, geoFilter = null) => {
  const params = { year };
  if (quarter) params.quarter = quarter;
  if (geoFilter) params.geo_filter = geoFilter;
  return api.get('/statistics/complete', { params });
};
