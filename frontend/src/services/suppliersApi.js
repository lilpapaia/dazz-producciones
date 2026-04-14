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
export const getBankCertUrl = (id, type = 'current') => api.get(`/suppliers/${id}/bank-cert-url`, { params: { cert_type: type } });
export const inviteSupplier = (data) => api.post('/suppliers/invite', data);
export const createOC = (data) => api.post('/suppliers/ocs', data);
export const checkOcNif = (nif) => api.get('/suppliers/ocs/check-nif', { params: { nif } });

export const exportSupplierExcel = (id) => api.get(`/suppliers/${id}/export-excel`, { responseType: 'blob' });

// Invoices
export const getInvoice = (id) => api.get(`/suppliers/invoices/${id}`);
export const getAllInvoices = (params) => api.get('/suppliers/invoices/all', { params });
export const updateInvoiceStatus = (id, data) => api.put(`/suppliers/invoices/${id}/status`, data);
export const deleteInvoice = (id, reason) => api.delete(`/suppliers/invoices/${id}`, { data: { reason } });
export const rejectInvoiceDeletion = (id, reason) => api.post(`/suppliers/invoices/${id}/reject-deletion`, { reason });
export const assignInvoiceOC = (invoiceId, ocNumber) => api.patch(`/suppliers/invoices/${invoiceId}/assign-oc`, { oc_number: ocNumber });

// OC autocomplete + prefixes
export const getOCSuggestions = (q) => api.get('/suppliers/oc-suggestions', { params: { q } });
export const getOCPrefixes = (permanentOnly = false) => api.get('/suppliers/ocs/prefixes', { params: { permanent_only: permanentOnly } });
export const validateOC = (oc) => api.get('/suppliers/ocs/validate-oc', { params: { oc } });

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

// Legal Documents
export const getLegalDocuments = (params) => api.get('/suppliers/legal-documents', { params });
export const getLegalDocumentStats = () => api.get('/suppliers/legal-documents/stats');
export const createLegalDocument = (formData, params) =>
  api.post('/suppliers/legal-documents', formData, { headers: { 'Content-Type': 'multipart/form-data' }, params });
export const deactivateLegalDocument = (id) => api.delete(`/suppliers/legal-documents/${id}`);
export const downloadLegalDocument = (id) => api.get(`/suppliers/legal-documents/${id}/download`);
export const getPendingSuppliers = (docId) => api.get(`/suppliers/legal-documents/${docId}/pending-suppliers`);
export const getLegalDocInfluencers = () => api.get('/suppliers/legal-documents/influencers');
export const extractLegalDocText = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/suppliers/legal-documents/extract-text', form, { headers: { 'Content-Type': 'multipart/form-data' } });
};
export const getSupplierDocuments = (supplierId) => api.get(`/suppliers/${supplierId}/documents`);
export const getBossContracts = () => api.get('/suppliers/legal-documents/boss-contracts');
export const inviteWithContract = (formData, params) =>
  api.post('/suppliers/invite-with-contract', formData, { headers: { 'Content-Type': 'multipart/form-data' }, params });

// Notifications
export const getNotifications = (params) => api.get('/suppliers/notifications/all', { params });
export const markNotificationRead = (id) => api.put(`/suppliers/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.put('/suppliers/notifications/read-all');
export const deleteNotification = (id) => api.delete(`/suppliers/notifications/${id}`);
export const deleteReadNotifications = () => api.delete('/suppliers/notifications/read');
