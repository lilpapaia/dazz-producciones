import { Component } from 'react';

/**
 * UX-H2: Error Boundary for supplier portal.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4">
          <div className="text-center max-w-sm">
            <h2 className="font-['Bebas_Neue'] text-xl text-zinc-100 mb-2">Something went wrong</h2>
            <p className="text-xs text-zinc-500 mb-6">An unexpected error occurred. Please reload the page.</p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-sm rounded-md transition-colors"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
