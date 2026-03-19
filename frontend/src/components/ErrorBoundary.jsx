import { Component } from 'react';

/**
 * UX-H2: Error Boundary — catches React rendering errors and shows a fallback UI
 * instead of a blank white screen. Class component required (hooks don't support componentDidCatch).
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-zinc-100 mb-2">Algo salió mal</h2>
            <p className="text-sm text-zinc-400 mb-6">
              Ha ocurrido un error inesperado. Puedes intentar recargar la página.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all"
            >
              RECARGAR PÁGINA
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
