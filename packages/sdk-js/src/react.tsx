/**
 * CodeWarden React Integration
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { CodeWarden } from './index';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode | ((props: { error: Error; resetError: () => void }) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * React Error Boundary that captures errors and sends them to CodeWarden.
 *
 * @example
 * ```tsx
 * import { CodeWardenErrorBoundary } from 'codewarden-js/react';
 *
 * function App() {
 *   return (
 *     <CodeWardenErrorBoundary fallback={<ErrorPage />}>
 *       <MyApp />
 *     </CodeWardenErrorBoundary>
 *   );
 * }
 * ```
 */
export class CodeWardenErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Capture to CodeWarden
    try {
      CodeWarden.captureException(error);
    } catch {
      // SDK not initialized, ignore
    }

    // Call custom handler
    this.props.onError?.(error, errorInfo);
  }

  resetError = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    const { children, fallback } = this.props;

    if (error) {
      if (!fallback) {
        return null;
      }

      if (typeof fallback === 'function') {
        return fallback({ error, resetError: this.resetError });
      }

      return fallback;
    }

    return children;
  }
}

/**
 * Hook to capture errors manually.
 *
 * @example
 * ```tsx
 * import { useCaptureException } from 'codewarden-js/react';
 *
 * function MyComponent() {
 *   const captureException = useCaptureException();
 *
 *   const handleClick = async () => {
 *     try {
 *       await riskyOperation();
 *     } catch (error) {
 *       captureException(error);
 *     }
 *   };
 *
 *   return <button onClick={handleClick}>Do something</button>;
 * }
 * ```
 */
export function useCaptureException(): (error: Error) => string {
  return (error: Error) => {
    try {
      return CodeWarden.captureException(error);
    } catch {
      // SDK not initialized
      console.error('[CodeWarden] SDK not initialized:', error);
      return '';
    }
  };
}

/**
 * Hook to capture messages manually.
 */
export function useCaptureMessage(): (message: string, level?: 'error' | 'warning' | 'info' | 'debug') => string {
  return (message: string, level: 'error' | 'warning' | 'info' | 'debug' = 'info') => {
    try {
      return CodeWarden.captureMessage(message, level);
    } catch {
      // SDK not initialized
      console.log(`[CodeWarden] ${level}: ${message}`);
      return '';
    }
  };
}
