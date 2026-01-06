# CodeWarden JavaScript SDK Reference

Complete reference documentation for the CodeWarden JavaScript/TypeScript SDK.

## Installation

```bash
npm install codewarden-js
# or
pnpm add codewarden-js
# or
yarn add codewarden-js
```

## Initialization

### `CodeWarden.init()`

Initialize the CodeWarden SDK. This must be called before any other SDK methods.

```typescript
import { CodeWarden } from 'codewarden-js';

const client = CodeWarden.init({
  dsn: 'https://your-api-key@api.codewarden.io/your-project-id',
  environment: 'production',      // Optional
  release: '1.0.0',               // Optional
  debug: false,                   // Optional
  enablePiiScrubbing: true,       // Optional (default: true)
  maxBreadcrumbs: 100,            // Optional (default: 100)
});
```

**Configuration Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dsn` | `string` | required | Your CodeWarden DSN from the dashboard |
| `environment` | `string` | `'production'` | Environment name |
| `release` | `string` | `undefined` | Release or version identifier |
| `debug` | `boolean` | `false` | Enable debug logging |
| `enablePiiScrubbing` | `boolean` | `true` | Enable automatic PII scrubbing |
| `maxBreadcrumbs` | `number` | `100` | Maximum breadcrumbs to retain |
| `beforeSend` | `function` | `undefined` | Hook to modify/filter events |

## Capturing Events

### `CodeWarden.captureException()`

Capture and send an error to CodeWarden.

```typescript
try {
  await processOrder(orderId);
} catch (error) {
  const eventId = CodeWarden.captureException(error);
  console.log(`Error captured: ${eventId}`);
}
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `error` | `Error` | The error to capture |

**Returns:** `string` - Event ID

### `CodeWarden.captureMessage()`

Capture and send a message to CodeWarden.

```typescript
// Info message (default)
CodeWarden.captureMessage('User completed checkout');

// Warning message
CodeWarden.captureMessage('API rate limit at 80%', 'warning');

// Error message
CodeWarden.captureMessage('Failed to sync with external service', 'error');

// Debug message
CodeWarden.captureMessage('Cache miss for key: user-prefs', 'debug');
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `string` | required | The message to send |
| `level` | `'debug' \| 'info' \| 'warning' \| 'error'` | `'info'` | Log level |

**Returns:** `string` - Event ID

## Context

### `CodeWarden.setContext()`

Set additional context that will be included with all captured events.

```typescript
// Set user context
CodeWarden.setContext({
  user_id: 'user-123',
  user_email: 'user@example.com',  // Will be scrubbed to [EMAIL]
  subscription: 'premium',
  organization_id: 'org-456',
});

// Context is included in all subsequent events
CodeWarden.captureMessage('User action');
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | `Record<string, unknown>` | Key-value pairs to include |

## React Integration

### `CodeWardenErrorBoundary`

A React Error Boundary that automatically captures errors and displays a fallback UI.

```tsx
import { CodeWardenErrorBoundary } from 'codewarden-js/react';

// Basic usage
function App() {
  return (
    <CodeWardenErrorBoundary fallback={<ErrorPage />}>
      <MyApp />
    </CodeWardenErrorBoundary>
  );
}

// With render prop fallback
function App() {
  return (
    <CodeWardenErrorBoundary
      fallback={({ error, resetError }) => (
        <div className="error-container">
          <h1>Something went wrong</h1>
          <pre>{error.message}</pre>
          <button onClick={resetError}>Try Again</button>
        </div>
      )}
      onError={(error, errorInfo) => {
        // Custom error handling
        console.error('Caught error:', error);
        console.error('Component stack:', errorInfo.componentStack);
      }}
    >
      <MyApp />
    </CodeWardenErrorBoundary>
  );
}
```

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `children` | `ReactNode` | Child components to wrap |
| `fallback` | `ReactNode \| ((props) => ReactNode)` | Fallback UI when error occurs |
| `onError` | `(error, errorInfo) => void` | Optional callback for custom handling |

**Fallback Props (render prop):**

| Prop | Type | Description |
|------|------|-------------|
| `error` | `Error` | The caught error |
| `resetError` | `() => void` | Function to reset the error boundary |

### `useCaptureException()`

Hook for capturing exceptions manually in functional components.

```tsx
import { useCaptureException } from 'codewarden-js/react';

function PaymentForm() {
  const captureException = useCaptureException();

  const handleSubmit = async (data: PaymentData) => {
    try {
      await processPayment(data);
    } catch (error) {
      captureException(error);
      toast.error('Payment failed. Please try again.');
    }
  };

  return <form onSubmit={handleSubmit}>...</form>;
}
```

**Returns:** `(error: Error) => string` - Capture function that returns event ID

### `useCaptureMessage()`

Hook for capturing messages in functional components.

```tsx
import { useCaptureMessage } from 'codewarden-js/react';

function FeatureComponent() {
  const captureMessage = useCaptureMessage();

  useEffect(() => {
    captureMessage('Feature component mounted', 'debug');

    return () => {
      captureMessage('Feature component unmounted', 'debug');
    };
  }, []);

  const handleImportantAction = () => {
    captureMessage('User performed important action', 'info');
  };

  return <button onClick={handleImportantAction}>Do Something</button>;
}
```

**Returns:** `(message: string, level?: LogLevel) => string`

## PII Scrubbing

The Airlock module automatically scrubs sensitive data from events.

### Default Patterns

| Type | Example | Replacement |
|------|---------|-------------|
| Email | `user@example.com` | `[EMAIL]` |
| Phone | `+1-555-123-4567` | `[PHONE]` |
| Credit Card | `4111-1111-1111-1111` | `[CARD]` |
| SSN | `123-45-6789` | `[SSN]` |
| IP Address | `192.168.1.1` | `[IP]` |
| API Keys | `sk_live_abc123...` | `[REDACTED]` |

### Manual Scrubbing

```typescript
import { Airlock } from 'codewarden-js';

const airlock = new Airlock();

// Scrub a string
const cleanText = airlock.scrub('Contact me at user@email.com');
// Result: 'Contact me at [EMAIL]'

// Scrub an object
const cleanData = airlock.scrubObject({
  email: 'user@test.com',
  phone: '555-123-4567',
  nested: {
    ssn: '123-45-6789',
  },
});
// Result: { email: '[EMAIL]', phone: '[PHONE]', nested: { ssn: '[SSN]' } }
```

### Custom Patterns

```typescript
import { Airlock } from 'codewarden-js';

const airlock = new Airlock({
  additionalPatterns: {
    employee_id: /EMP-\d{6}/g,
    internal_token: /INT_[A-Z0-9]{32}/g,
  },
});
```

## Framework Integrations

### Next.js (App Router)

```typescript
// app/providers.tsx
'use client';

import { useEffect } from 'react';
import { CodeWarden } from 'codewarden-js';
import { CodeWardenErrorBoundary } from 'codewarden-js/react';

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    CodeWarden.init({
      dsn: process.env.NEXT_PUBLIC_CODEWARDEN_DSN!,
      environment: process.env.NODE_ENV,
      release: process.env.NEXT_PUBLIC_APP_VERSION,
    });
  }, []);

  return (
    <CodeWardenErrorBoundary
      fallback={<div>Something went wrong</div>}
    >
      {children}
    </CodeWardenErrorBoundary>
  );
}

// app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### Next.js (Pages Router)

```typescript
// pages/_app.tsx
import type { AppProps } from 'next/app';
import { useEffect } from 'react';
import { CodeWarden } from 'codewarden-js';
import { CodeWardenErrorBoundary } from 'codewarden-js/react';

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    CodeWarden.init({
      dsn: process.env.NEXT_PUBLIC_CODEWARDEN_DSN!,
      environment: process.env.NODE_ENV,
    });
  }, []);

  return (
    <CodeWardenErrorBoundary>
      <Component {...pageProps} />
    </CodeWardenErrorBoundary>
  );
}
```

### Vite / Create React App

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { CodeWarden } from 'codewarden-js';
import { CodeWardenErrorBoundary } from 'codewarden-js/react';
import App from './App';

// Initialize CodeWarden
CodeWarden.init({
  dsn: import.meta.env.VITE_CODEWARDEN_DSN,
  environment: import.meta.env.MODE,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CodeWardenErrorBoundary
      fallback={<div>Application Error</div>}
    >
      <App />
    </CodeWardenErrorBoundary>
  </React.StrictMode>
);
```

## Client API

### `CodeWardenClient`

For advanced usage, you can instantiate the client directly:

```typescript
import { CodeWardenClient } from 'codewarden-js';

const client = new CodeWardenClient({
  dsn: 'https://...',
  environment: 'production',
  beforeSend: (event) => {
    // Modify event before sending
    if (event.context?.user_id === 'test-user') {
      return null; // Don't send test events
    }
    return event;
  },
});

// Use the client
client.captureException(error);
client.captureMessage('Custom message');

// Set context
client.setContext({ key: 'value' });

// Close and flush
await client.close();
```

### `beforeSend` Hook

Filter or modify events before they're sent:

```typescript
CodeWarden.init({
  dsn: '...',
  beforeSend: (event) => {
    // Filter out specific errors
    if (event.exception?.type === 'NetworkError') {
      return null;
    }

    // Add custom data
    event.tags = {
      ...event.tags,
      app_version: '1.0.0',
    };

    return event;
  },
});
```

## TypeScript Types

```typescript
import type {
  CodeWardenConfig,
  Event,
  EventContext,
  ExceptionInfo,
  StackFrame,
  LogLevel,
} from 'codewarden-js';

// Configuration type
const config: CodeWardenConfig = {
  dsn: 'https://...',
  environment: 'production',
};

// Event structure
interface Event {
  event_id: string;
  timestamp: string;
  level: LogLevel;
  message?: string;
  exception?: ExceptionInfo;
  context?: EventContext;
  breadcrumbs?: Breadcrumb[];
}

// Log levels
type LogLevel = 'debug' | 'info' | 'warning' | 'error';
```

## Browser Support

The SDK supports all modern browsers:

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

For older browsers, ensure you have appropriate polyfills for:
- `fetch`
- `Promise`
- `Array.from`

## Best Practices

### 1. Initialize Early

```typescript
// Initialize before any rendering
CodeWarden.init({ dsn: '...' });

// Then render your app
ReactDOM.createRoot(root).render(<App />);
```

### 2. Use Error Boundaries at Multiple Levels

```tsx
function App() {
  return (
    <CodeWardenErrorBoundary fallback={<AppError />}>
      <Header />
      <CodeWardenErrorBoundary fallback={<ContentError />}>
        <MainContent />
      </CodeWardenErrorBoundary>
      <Footer />
    </CodeWardenErrorBoundary>
  );
}
```

### 3. Add User Context After Authentication

```typescript
function useAuthSync() {
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      CodeWarden.setContext({
        user_id: user.id,
        user_email: user.email,
        user_role: user.role,
      });
    }
  }, [user]);
}
```

### 4. Handle Async Errors

```typescript
// In React components
function DataLoader() {
  const captureException = useCaptureException();

  useEffect(() => {
    fetchData()
      .catch((error) => {
        captureException(error);
        setError('Failed to load data');
      });
  }, []);
}

// Outside React
window.addEventListener('unhandledrejection', (event) => {
  CodeWarden.captureException(event.reason);
});
```

### 5. Clean Up on Unmount

```typescript
// In your app's cleanup
useEffect(() => {
  return () => {
    CodeWarden.close();
  };
}, []);
```
