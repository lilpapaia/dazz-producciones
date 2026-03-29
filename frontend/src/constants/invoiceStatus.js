/**
 * Shared invoice status constants for the suppliers admin module.
 * Used by InvoicesList, InvoiceDetail, and other supplier pages.
 */

export const INVOICE_PILL = {
  PENDING: { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500' },
  OC_PENDING: { cls: 'bg-blue-400/10 text-blue-400 border-blue-400/20', dot: 'bg-blue-400' },
  APPROVED: { cls: 'bg-green-400/10 text-green-400 border-green-400/20', dot: 'bg-green-400' },
  PAID: { cls: 'bg-green-300/10 text-green-300 border-green-300/20', dot: 'bg-green-300' },
  DELETE_REQUESTED: { cls: 'bg-red-300/10 text-red-300 border-red-300/20', dot: 'bg-red-300' },
};

export const INVOICE_LABEL = {
  PENDING: 'Pendiente',
  OC_PENDING: 'OC pendiente',
  APPROVED: 'Aprobada',
  PAID: 'Pagada',
  DELETE_REQUESTED: 'Borrado solicitado',
};
