import api from './api';

// Dashboard
export const getSuppliersDashboard = () => api.get('/suppliers/dashboard/stats');

// Suppliers CRUD
export const getSuppliers = (params) => api.get('/suppliers', { params });
export const getSupplier = (id) => api.get(`/suppliers/${id}`);
export const updateSupplier = (id, data) => api.put(`/suppliers/${id}`, data);
export const deactivateSupplier = (id) => api.put(`/suppliers/${id}/deactivate`);
export const assignOC = (id, ocNumber) => api.put(`/suppliers/${id}/assign-oc`, { oc_number: ocNumber });
export const addSupplierNote = (id, note) => api.post(`/suppliers/${id}/notes`, { note });
export const getBankCertUrl = (id) => api.get(`/suppliers/${id}/bank-cert-url`);
export const inviteSupplier = (data) => api.post('/suppliers/invite', data);
export const createOC = (data) => api.post('/suppliers/ocs', data);

export const exportSupplierExcel = (id) => api.get(`/suppliers/${id}/export-excel`, { responseType: 'blob' });

// Invoices
export const getInvoice = (id) => api.get(`/suppliers/invoices/${id}`);
export const getAllInvoices = (params) => api.get('/suppliers/invoices/all', { params });
export const updateInvoiceStatus = (id, data) => api.put(`/suppliers/invoices/${id}/status`, data);
export const deleteInvoice = (id) => api.delete(`/suppliers/invoices/${id}`);

// Notifications
export const getNotifications = (params) => api.get('/suppliers/notifications/all', { params });
export const markNotificationRead = (id) => api.put(`/suppliers/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.put('/suppliers/notifications/read-all');
