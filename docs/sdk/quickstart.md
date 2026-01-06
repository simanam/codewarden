# CodeWarden Quickstart Guide

Get started with CodeWarden in under 5 minutes. This guide covers installation and basic setup for Python and JavaScript applications.

## Prerequisites

- A CodeWarden account with an active project
- Your API key from the CodeWarden dashboard

## Python SDK

### Installation

```bash
pip install codewarden
```

Or with Poetry:

```bash
poetry add codewarden
```

### Basic Setup

```python
import codewarden

# Initialize the SDK with your DSN
codewarden.init(
    dsn="https://your-api-key@api.codewarden.io/your-project-id",
    environment="production",
    release="1.0.0"
)

# Capture exceptions
try:
    risky_operation()
except Exception as e:
    codewarden.capture_exception(e)

# Capture messages
codewarden.capture_message("User signed up", level="info")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from codewarden.middleware import CodeWardenMiddleware

app = FastAPI()

# Add CodeWarden middleware
app.add_middleware(
    CodeWardenMiddleware,
    capture_exceptions=True,
    excluded_paths=["/health", "/metrics"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### Adding Breadcrumbs

Breadcrumbs help you understand what happened before an error:

```python
import codewarden

# Add breadcrumbs to provide context
codewarden.add_breadcrumb("ui", "User clicked checkout button")
codewarden.add_breadcrumb("http", "POST /api/orders", data={"items": 3})
codewarden.add_breadcrumb("database", "Inserted order record")

# When an error occurs, breadcrumbs are included automatically
try:
    process_payment()
except Exception as e:
    codewarden.capture_exception(e)  # Includes all breadcrumbs
```

## JavaScript/TypeScript SDK

### Installation

```bash
npm install codewarden-js
# or
pnpm add codewarden-js
# or
yarn add codewarden-js
```

### Basic Setup

```typescript
import { CodeWarden } from 'codewarden-js';

// Initialize the SDK
CodeWarden.init({
  dsn: 'https://your-api-key@api.codewarden.io/your-project-id',
  environment: 'production',
  release: '1.0.0',
});

// Capture exceptions
try {
  riskyOperation();
} catch (error) {
  CodeWarden.captureException(error);
}

// Capture messages
CodeWarden.captureMessage('User completed onboarding', 'info');
```

### React Integration

```tsx
import { CodeWardenErrorBoundary, useCaptureException } from 'codewarden-js/react';

// Wrap your app with the error boundary
function App() {
  return (
    <CodeWardenErrorBoundary
      fallback={({ error, resetError }) => (
        <div>
          <h1>Something went wrong</h1>
          <p>{error.message}</p>
          <button onClick={resetError}>Try again</button>
        </div>
      )}
    >
      <MyApp />
    </CodeWardenErrorBoundary>
  );
}

// Use the hook for manual error capture
function CheckoutButton() {
  const captureException = useCaptureException();

  const handleClick = async () => {
    try {
      await processPayment();
    } catch (error) {
      captureException(error);
      showErrorToast('Payment failed');
    }
  };

  return <button onClick={handleClick}>Checkout</button>;
}
```

### Next.js Integration

```typescript
// app/layout.tsx
import { CodeWarden } from 'codewarden-js';

// Initialize on the client side
if (typeof window !== 'undefined') {
  CodeWarden.init({
    dsn: process.env.NEXT_PUBLIC_CODEWARDEN_DSN!,
    environment: process.env.NODE_ENV,
  });
}

export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
```

## Getting Your DSN

1. Log in to [CodeWarden Dashboard](https://app.codewarden.io)
2. Navigate to **Projects**
3. Click on your project (or create one)
4. Click the **Key** icon to manage API keys
5. Copy your DSN from the displayed format

Your DSN looks like: `https://cw_live_xxxx@api.codewarden.io/project-id`

## Environment Variables

We recommend storing your DSN in environment variables:

```bash
# .env
CODEWARDEN_DSN=https://cw_live_xxxx@api.codewarden.io/project-id
```

```python
# Python
import os
import codewarden

codewarden.init(dsn=os.environ["CODEWARDEN_DSN"])
```

```typescript
// JavaScript/TypeScript
CodeWarden.init({ dsn: process.env.CODEWARDEN_DSN });
```

## What's Next?

- [Python SDK Reference](./python-sdk.md) - Full API documentation
- [JavaScript SDK Reference](./javascript-sdk.md) - Full API documentation
- [PII Scrubbing](./python-sdk.md#pii-scrubbing) - Automatic sensitive data protection
- [Dashboard Guide](../dashboard.md) - View and analyze your events
