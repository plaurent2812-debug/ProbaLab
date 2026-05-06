import { Component, type ErrorInfo, type ReactNode } from 'react';
import ErrorPage from '@/pages/ErrorPage';

interface State {
  error: Error | null;
}

interface Props {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback(this.state.error);
      return <ErrorPage error={this.state.error} />;
    }
    return this.props.children;
  }
}
