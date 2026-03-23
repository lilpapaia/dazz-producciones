import { useEffect } from 'react';

/**
 * UX-L2: Hook to close modals/overlays with Escape key.
 * @param {Function} callback - Called when Escape is pressed
 * @param {boolean} enabled - Whether the listener is active (default true)
 */
const useEscapeKey = (callback, enabled = true) => {
  useEffect(() => {
    if (!enabled) return;
    const handler = (e) => {
      if (e.key === 'Escape') callback();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [callback, enabled]);
};

export default useEscapeKey;
