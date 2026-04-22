import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    const msg = error?.message ?? '';
    if (
      msg.includes('Failed to fetch dynamically imported module') ||
      msg.includes('Loading chunk') ||
      msg.includes('Loading CSS chunk')
    ) {
      window.location.reload();
      return;
    }
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary (V2) caught:', error, info);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback;
    return (
      <div
        data-testid="error-boundary-fallback"
        role="alert"
        style={{
          minHeight: '60vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          padding: 24,
          textAlign: 'center',
          color: 'var(--text)',
          background: 'var(--bg)',
        }}
      >
        <h2 style={{ fontSize: 22, fontWeight: 700 }}>Une erreur est survenue</h2>
        <p style={{ maxWidth: 420, color: 'var(--text-muted)' }}>
          Pas de panique — la page a planté à l'affichage. On a capturé l'erreur,
          vous pouvez relancer la vue sans recharger la page.
        </p>
        <button
          type="button"
          onClick={this.handleRetry}
          style={{
            padding: '10px 18px',
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: 'var(--primary)',
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;
