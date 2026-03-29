/**
 * UX-H1: Toast notification helpers.
 * Wraps sonner with consistent styling matching zinc/amber design system.
 */
import { toast } from 'sonner';

export const showSuccess = (message) =>
  toast.success(message, { duration: 3000 });

export const showError = (message) =>
  toast.error(message, { duration: 5000 });

export const showWarning = (message) =>
  toast.warning(message, { duration: 4000 });
