# CodeWarden JavaScript SDK

Security and observability SDK for JavaScript and TypeScript applications.

## Installation

```bash
npm install codewarden-js
```

## Quick Start

```typescript
import { CodeWarden } from 'codewarden-js';

// Initialize with your DSN (get it from https://codewarden.io)
CodeWarden.init({
  dsn: 'cw_live_YOUR_API_KEY@api.codewarden.io',
  environment: 'production',
});

// Capture messages
CodeWarden.captureMessage('User signed up successfully');

// Capture exceptions
try {
  riskyOperation();
} catch (error) {
  CodeWarden.captureException(error);
}

// Set user context
CodeWarden.setUser({ id: 'user-123', email: 'user@example.com' });
```

## React Integration

```tsx
import { CodeWardenErrorBoundary } from 'codewarden-js/react';

function App() {
  return (
    <CodeWardenErrorBoundary fallback={<ErrorPage />}>
      <MyApp />
    </CodeWardenErrorBoundary>
  );
}
```

### React Hooks

```tsx
import { useCaptureException, useCaptureMessage } from 'codewarden-js/react';

function MyComponent() {
  const captureException = useCaptureException();
  const captureMessage = useCaptureMessage();

  const handleClick = async () => {
    try {
      await riskyOperation();
      captureMessage('Operation succeeded', 'info');
    } catch (error) {
      captureException(error);
    }
  };

  return <button onClick={handleClick}>Do something</button>;
}
```

## Features

- **Error Tracking**: Automatic exception capture with full stack traces
- **PII Scrubbing**: Automatically redacts sensitive data (emails, credit cards, etc.)
- **React Integration**: Error boundaries and hooks for React apps
- **TypeScript Support**: Full type definitions included
- **Lightweight**: Tree-shakeable, minimal bundle impact

## Configuration Options

```typescript
CodeWarden.init({
  dsn: 'cw_live_xxx@api.codewarden.io',
  environment: 'production',     // Environment name
  release: '1.0.0',              // Your app version
  enablePiiScrubbing: true,      // Auto-scrub sensitive data
  debug: false,                  // Enable debug logging
  beforeSend: (event) => {       // Hook to modify/filter events
    // Return null to drop the event
    return event;
  },
});
```

## Links

- [Dashboard](https://codewarden.io)
- [Documentation](https://codewarden.io/docs)
- [GitHub](https://github.com/simanam/codewarden)

## License

MIT License - see [LICENSE](../../LICENSE) for details.
