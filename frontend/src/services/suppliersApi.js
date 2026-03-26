import api from './api';

// Dashboard
export const getSuppliersDashboard = () => api.get('/suppliers/dashboard/stats');

// Suppliers CRUD
export const getSuppliers = (params) => api.get('/suppliers', { params });
export const getSupplier = (id) => api.get(`/suppliers/${id}`);
export const updateSupplier = (id, data) => api.put(`/suppliers/${id}`, data);
export const deactivateSupplier = (id) => api.put(`/suppliers/${id}/deactivate`);
export const reactivateSupplier = (id) => api.put(`/suppliers/${id}/reactivate`);
export const assignOC = (id, ocNumber) => api.put(`/suppliers/${id}/assign-oc`, { oc_number: ocNumber });
export const addSupplierNote = (id, note) => api.post(`/suppliers/${id}/notes`, { note });
export const getBankCertUrl = (id) => api.get(`/suppliers/${id}/bank-cert-url`);
export const inviteSupplier = (data) => api.post('/suppliers/invite', data);
export const createOC = (data) => api.post('/suppliers/ocs', data);
export const checkOcNif = (nif) => api.get('/suppliers/ocs/check-nif', { params: { nif } });

export const exportSupplierExcel = (id) => api.get(`/suppliers/${id}/export-excel`, { responseType: 'blob' });

// Invoices
export const getInvoice = (id) => api.get(`/suppliers/invoices/${id}`);
export const getAllInvoices = (params) => api.get('/suppliers/invoices/all', { params });
export const updateInvoiceStatus = (id, data) => api.put(`/suppliers/invoices/${id}/status`, data);
export const deleteInvoice = (id, reason) => api.delete(`/suppliers/invoices/${id}`, { data: { reason } });
export const assignInvoiceOC = (invoiceId, ocNumber) => api.patch(`/suppliers/invoices/${invoiceId}/assign-oc`, { oc_number: ocNumber });

// OC autocomplete
export const getOCSuggestions = (q) => api.get('/suppliers/oc-suggestions', { params: { q } });

// Autoinvoice
export const getNextInvoiceNumber = (companyId) => api.get('/suppliers/autoinvoice/next-number', { params: { company_id: companyId } });
export const searchSuppliersForAutoinvoice = (q) => api.get('/suppliers/autoinvoice/supplier-search', { params: { q } });
export const generateAutoinvoice = (data) => api.post('/suppliers/autoinvoice/generate', data);
export const previewAutoinvoice = (data) => api.post('/suppliers/autoinvoice/preview', data, { responseType: 'blob' });

// Pending Actions
export const getPendingActions = (id) => api.get(`/suppliers/${id}/pending-actions`);
export const approveDataChange = (id, notifId) => api.post(`/suppliers/${id}/approve-data-change`, { notification_id: notifId });
export const rejectDataChange = (id, notifId, reason) => api.post(`/suppliers/${id}/reject-data-change`, { notification_id: notifId, reason });
export const approveIbanChange = (id, notifId) => api.post(`/suppliers/${id}/approve-iban-change`, { notification_id: notifId });
export const rejectIbanChange = (id, notifId, reason) => api.post(`/suppliers/${id}/reject-iban-change`, { notification_id: notifId, reason });
export const confirmDeactivation = (id, notifId) => api.post(`/suppliers/${id}/confirm-deactivation`, { notification_id: notifId });
export const rejectDeactivation = (id, notifId, reason) => api.post(`/suppliers/${id}/reject-deactivation`, { notification_id: notifId, reason });
export const verifyCert = (id) => api.post(`/suppliers/${id}/verify-cert`);

// Notifications
export const getNotifications = (params) => api.get('/suppliers/notifications/all', { params });
export const markNotificationRead = (id) => api.put(`/suppliers/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.put('/suppliers/notifications/read-all');
