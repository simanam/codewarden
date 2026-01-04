# CodeWarden Implementation Checklist
## Part 3: Frontend, Integration & Launch

**Document Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2026  
**Estimated Duration:** Weeks 7-10

---

## Document Navigation

| Part | Focus Area | Status |
|------|------------|--------|
| Part 1 | Foundation & Infrastructure Setup | ✅ Complete |
| Part 2 | Core Product Development (SDK + API) | ✅ Complete |
| **Part 3** | Frontend, Integration & Launch | 📍 Current |

---

## Prerequisites

Before starting Part 3, ensure:
- [ ] Part 1 & Part 2 completed
- [ ] Python SDK fully functional
- [ ] API endpoints working
- [ ] All backend tests passing

---

# Phase 3: JavaScript SDK Development

## Story 3.1: JavaScript SDK Setup

### Task 3.1.1: Initialize JavaScript SDK Package

**Sub-tasks:**

- [ ] **3.1.1.1** Create package structure
  ```bash
  cd packages/sdk-js
  
  # Initialize package
  pnpm init
  
  # Create directories
  mkdir -p src/{middleware,guards,scrubber,transport,types}
  mkdir -p tests/{unit,integration}
  ```

- [ ] **3.1.1.2** Create `package.json`
  ```bash
  cat > package.json << 'EOF'
  {
    "name": "codewarden-js",
    "version": "0.1.0",
    "description": "CodeWarden JavaScript SDK - Security monitoring for solopreneurs",
    "main": "dist/index.js",
    "module": "dist/index.mjs",
    "types": "dist/index.d.ts",
    "exports": {
      ".": {
        "require": "./dist/index.js",
        "import": "./dist/index.mjs",
        "types": "./dist/index.d.ts"
      }
    },
    "files": [
      "dist"
    ],
    "scripts": {
      "build": "tsup src/index.ts --format cjs,esm --dts",
      "dev": "tsup src/index.ts --format cjs,esm --dts --watch",
      "test": "vitest run",
      "test:watch": "vitest",
      "test:coverage": "vitest run --coverage",
      "lint": "eslint src --ext .ts,.tsx",
      "lint:fix": "eslint src --ext .ts,.tsx --fix",
      "typecheck": "tsc --noEmit",
      "clean": "rm -rf dist",
      "prepublishOnly": "pnpm build"
    },
    "keywords": [
      "security",
      "monitoring",
      "observability",
      "nextjs",
      "error-tracking",
      "sentry-alternative"
    ],
    "author": "CodeWarden <hello@codewarden.io>",
    "license": "MIT",
    "repository": {
      "type": "git",
      "url": "https://github.com/codewarden/codewarden.git",
      "directory": "packages/sdk-js"
    },
    "homepage": "https://codewarden.io",
    "bugs": {
      "url": "https://github.com/codewarden/codewarden/issues"
    },
    "peerDependencies": {
      "next": ">=13.0.0",
      "react": ">=18.0.0"
    },
    "peerDependenciesMeta": {
      "next": {
        "optional": true
      },
      "react": {
        "optional": true
      }
    },
    "devDependencies": {
      "@types/node": "^20.11.0",
      "@types/react": "^18.2.48",
      "@typescript-eslint/eslint-plugin": "^6.19.0",
      "@typescript-eslint/parser": "^6.19.0",
      "@vitest/coverage-v8": "^1.2.0",
      "eslint": "^8.56.0",
      "eslint-config-prettier": "^9.1.0",
      "eslint-plugin-prettier": "^5.1.3",
      "next": "^14.1.0",
      "prettier": "^3.2.4",
      "react": "^18.2.0",
      "tsup": "^8.0.1",
      "typescript": "^5.3.3",
      "vitest": "^1.2.0"
    }
  }
  EOF
  ```

- [ ] **3.1.1.3** Create `tsconfig.json`
  ```bash
  cat > tsconfig.json << 'EOF'
  {
    "compilerOptions": {
      "target": "ES2020",
      "module": "ESNext",
      "moduleResolution": "bundler",
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "strict": true,
      "esModuleInterop": true,
      "skipLibCheck": true,
      "forceConsistentCasingInFileNames": true,
      "resolveJsonModule": true,
      "isolatedModules": true,
      "declaration": true,
      "declarationMap": true,
      "sourceMap": true,
      "outDir": "./dist",
      "rootDir": "./src",
      "jsx": "react-jsx",
      "types": ["node"]
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist", "tests"]
  }
  EOF
  ```

- [ ] **3.1.1.4** Create ESLint configuration
  ```bash
  cat > .eslintrc.json << 'EOF'
  {
    "parser": "@typescript-eslint/parser",
    "extends": [
      "eslint:recommended",
      "plugin:@typescript-eslint/recommended",
      "plugin:prettier/recommended"
    ],
    "plugins": ["@typescript-eslint"],
    "env": {
      "browser": true,
      "node": true,
      "es2020": true
    },
    "rules": {
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-explicit-any": "warn"
    }
  }
  EOF
  ```

- [ ] **3.1.1.5** Install dependencies
  ```bash
  pnpm install
  ```

**Testing:**
- [ ] Run `pnpm build` → Builds successfully
- [ ] Run `pnpm typecheck` → No errors

---

### Task 3.1.2: Implement TypeScript Types

**Sub-tasks:**

- [ ] **3.1.2.1** Create `src/types/index.ts`
  ```bash
  cat > src/types/index.ts << 'EOF'
  /**
   * CodeWarden TypeScript type definitions.
   */
  
  /**
   * CodeWarden configuration options.
   */
  export interface CodeWardenConfig {
    /** Your CodeWarden API key */
    apiKey?: string;
    
    /** API endpoint URL */
    apiUrl?: string;
    
    /** Enable/disable CodeWarden */
    enabled?: boolean;
    
    /** Enable PII scrubbing */
    scrubPii?: boolean;
    
    /** Capture unhandled errors */
    captureErrors?: boolean;
    
    /** Capture console output */
    captureConsole?: boolean;
    
    /** Track network requests */
    captureNetwork?: boolean;
    
    /** Environment name */
    environment?: string;
    
    /** Debug mode */
    debug?: boolean;
  }
  
  /**
   * Telemetry event payload.
   */
  export interface TelemetryPayload {
    source: string;
    type: 'crash' | 'request' | 'log' | 'custom';
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    environment: string;
    payload: Record<string, unknown>;
    timestamp: string;
  }
  
  /**
   * Error event details.
   */
  export interface ErrorEvent {
    errorType: string;
    errorMessage: string;
    stackTrace?: string;
    componentStack?: string;
    url?: string;
    userAgent?: string;
    context?: Record<string, unknown>;
  }
  
  /**
   * Network request event.
   */
  export interface NetworkEvent {
    url: string;
    method: string;
    status?: number;
    statusText?: string;
    duration?: number;
    error?: string;
  }
  
  /**
   * Scrubbing result.
   */
  export interface ScrubResult {
    originalLength: number;
    scrubbedLength: number;
    patternsMatched: string[];
    isSafe: boolean;
  }
  
  /**
   * API response for telemetry.
   */
  export interface TelemetryResponse {
    id: string;
    status: 'queued' | 'processing' | 'complete';
  }
  EOF
  ```

---

### Task 3.1.3: Implement Airlock (JavaScript)

**Sub-tasks:**

- [ ] **3.1.3.1** Create `src/scrubber/patterns.ts`
  ```bash
  cat > src/scrubber/patterns.ts << 'EOF'
  /**
   * PII detection patterns for JavaScript.
   * Based on Gitleaks patterns.
   */
  
  export interface ScrubPattern {
    name: string;
    pattern: RegExp;
    replacement: string;
    category: 'identity' | 'financial' | 'api_key' | 'auth_token' | 'credential';
  }
  
  export const PATTERNS: Record<string, ScrubPattern> = {
    // Identity
    email: {
      name: 'email',
      pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
      replacement: '[EMAIL_REDACTED]',
      category: 'identity',
    },
    phone: {
      name: 'phone',
      pattern: /\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b/g,
      replacement: '[PHONE_REDACTED]',
      category: 'identity',
    },
    ssn: {
      name: 'ssn',
      pattern: /\b\d{3}-\d{2}-\d{4}\b/g,
      replacement: '[SSN_REDACTED]',
      category: 'identity',
    },
    
    // Financial
    creditCard: {
      name: 'credit_card',
      pattern: /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b/g,
      replacement: '[CC_REDACTED]',
      category: 'financial',
    },
    creditCardFormatted: {
      name: 'credit_card_formatted',
      pattern: /\b(?:\d{4}[- ]?){3}\d{4}\b/g,
      replacement: '[CC_REDACTED]',
      category: 'financial',
    },
    
    // API Keys
    openaiKey: {
      name: 'openai_key',
      pattern: /sk-[a-zA-Z0-9]{48,}/g,
      replacement: '[OPENAI_KEY_REDACTED]',
      category: 'api_key',
    },
    stripeKey: {
      name: 'stripe_key',
      pattern: /sk_(live|test)_[a-zA-Z0-9]{24,}/g,
      replacement: '[STRIPE_KEY_REDACTED]',
      category: 'api_key',
    },
    awsAccessKey: {
      name: 'aws_access_key',
      pattern: /(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}/g,
      replacement: '[AWS_KEY_REDACTED]',
      category: 'api_key',
    },
    googleApiKey: {
      name: 'google_api_key',
      pattern: /AIza[0-9A-Za-z\-_]{35}/g,
      replacement: '[GOOGLE_KEY_REDACTED]',
      category: 'api_key',
    },
    githubToken: {
      name: 'github_token',
      pattern: /gh[pousr]_[A-Za-z0-9_]{36,}/g,
      replacement: '[GITHUB_TOKEN_REDACTED]',
      category: 'api_key',
    },
    
    // Auth Tokens
    jwt: {
      name: 'jwt',
      pattern: /eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+/g,
      replacement: '[JWT_REDACTED]',
      category: 'auth_token',
    },
    bearerToken: {
      name: 'bearer_token',
      pattern: /bearer\s+[a-zA-Z0-9\-_.]+/gi,
      replacement: 'Bearer [TOKEN_REDACTED]',
      category: 'auth_token',
    },
    
    // Credentials
    passwordField: {
      name: 'password_field',
      pattern: /(password|passwd|pwd|secret)\s*[:=]\s*['"]?[^\s'"]+['"]?/gi,
      replacement: '$1=[PASSWORD_REDACTED]',
      category: 'credential',
    },
  };
  EOF
  ```

- [ ] **3.1.3.2** Create `src/scrubber/airlock.ts`
  ```bash
  cat > src/scrubber/airlock.ts << 'EOF'
  /**
   * Airlock - Client-side PII scrubbing for JavaScript.
   */
  
  import { PATTERNS, ScrubPattern } from './patterns';
  import { ScrubResult } from '../types';
  
  export interface AirlockOptions {
    /** Patterns to enable (defaults to all) */
    enabledPatterns?: string[];
    /** Custom patterns to add */
    customPatterns?: Record<string, ScrubPattern>;
  }
  
  export class Airlock {
    private patterns: Map<string, ScrubPattern>;
  
    constructor(options: AirlockOptions = {}) {
      this.patterns = new Map();
      
      // Add enabled patterns
      const enabledNames = options.enabledPatterns || Object.keys(PATTERNS);
      for (const name of enabledNames) {
        if (PATTERNS[name]) {
          this.patterns.set(name, PATTERNS[name]);
        }
      }
      
      // Add custom patterns
      if (options.customPatterns) {
        for (const [name, pattern] of Object.entries(options.customPatterns)) {
          this.patterns.set(name, pattern);
        }
      }
    }
  
    /**
     * Scrub PII from text.
     */
    scrub(text: string): string {
      if (!text) return text;
      
      let result = text;
      
      for (const pattern of this.patterns.values()) {
        // Reset regex lastIndex for global patterns
        pattern.pattern.lastIndex = 0;
        result = result.replace(pattern.pattern, pattern.replacement);
      }
      
      return result;
    }
  
    /**
     * Scrub PII from an object recursively.
     */
    scrubObject<T extends Record<string, unknown>>(obj: T): T {
      const result: Record<string, unknown> = {};
      
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === 'string') {
          result[key] = this.scrub(value);
        } else if (Array.isArray(value)) {
          result[key] = this.scrubArray(value);
        } else if (value !== null && typeof value === 'object') {
          result[key] = this.scrubObject(value as Record<string, unknown>);
        } else {
          result[key] = value;
        }
      }
      
      return result as T;
    }
  
    /**
     * Scrub PII from an array.
     */
    private scrubArray(arr: unknown[]): unknown[] {
      return arr.map((item) => {
        if (typeof item === 'string') {
          return this.scrub(item);
        } else if (Array.isArray(item)) {
          return this.scrubArray(item);
        } else if (item !== null && typeof item === 'object') {
          return this.scrubObject(item as Record<string, unknown>);
        }
        return item;
      });
    }
  
    /**
     * Check if text contains detectable PII.
     */
    isSafe(text: string): boolean {
      for (const pattern of this.patterns.values()) {
        pattern.pattern.lastIndex = 0;
        if (pattern.pattern.test(text)) {
          return false;
        }
      }
      return true;
    }
  
    /**
     * Detect which patterns match in text.
     */
    detect(text: string): string[] {
      const matches: string[] = [];
      
      for (const [name, pattern] of this.patterns.entries()) {
        pattern.pattern.lastIndex = 0;
        if (pattern.pattern.test(text)) {
          matches.push(name);
        }
      }
      
      return matches;
    }
  
    /**
     * Get scrubbing statistics.
     */
    getStats(text: string): ScrubResult {
      const matches = this.detect(text);
      const scrubbed = this.scrub(text);
      
      return {
        originalLength: text.length,
        scrubbedLength: scrubbed.length,
        patternsMatched: matches,
        isSafe: matches.length === 0,
      };
    }
  }
  EOF
  ```

- [ ] **3.1.3.3** Create `src/scrubber/index.ts`
  ```bash
  cat > src/scrubber/index.ts << 'EOF'
  export { Airlock, AirlockOptions } from './airlock';
  export { PATTERNS, ScrubPattern } from './patterns';
  EOF
  ```

**Testing:**
- [ ] Create unit tests for Airlock
- [ ] Run `pnpm test` → All tests pass

---

### Task 3.1.4: Implement Guards

**Sub-tasks:**

- [ ] **3.1.4.1** Create `src/guards/console.ts`
  ```bash
  cat > src/guards/console.ts << 'EOF'
  /**
   * Console Guard - Prevents accidental secret leakage in browser console.
   */
  
  import { Airlock } from '../scrubber';
  
  type ConsoleMethod = 'log' | 'warn' | 'error' | 'info' | 'debug';
  
  interface ConsoleGuardOptions {
    /** Console methods to guard */
    methods?: ConsoleMethod[];
    /** Block output entirely if secrets detected */
    blockSecrets?: boolean;
    /** Callback when secrets detected */
    onSecretDetected?: (method: ConsoleMethod, args: unknown[]) => void;
  }
  
  export class ConsoleGuard {
    private airlock: Airlock;
    private originalConsole: Partial<Record<ConsoleMethod, (...args: unknown[]) => void>>;
    private options: ConsoleGuardOptions;
    private installed = false;
  
    constructor(airlock: Airlock, options: ConsoleGuardOptions = {}) {
      this.airlock = airlock;
      this.originalConsole = {};
      this.options = {
        methods: ['log', 'warn', 'error', 'info'],
        blockSecrets: true,
        ...options,
      };
    }
  
    /**
     * Install console guards.
     */
    install(): void {
      if (this.installed || typeof console === 'undefined') return;
      
      for (const method of this.options.methods || []) {
        this.originalConsole[method] = console[method].bind(console);
        
        console[method] = (...args: unknown[]) => {
          const processedArgs = this.processArgs(args, method);
          
          if (processedArgs !== null) {
            this.originalConsole[method]?.(...processedArgs);
          }
        };
      }
      
      this.installed = true;
    }
  
    /**
     * Uninstall console guards.
     */
    uninstall(): void {
      if (!this.installed) return;
      
      for (const method of this.options.methods || []) {
        if (this.originalConsole[method]) {
          console[method] = this.originalConsole[method] as typeof console.log;
        }
      }
      
      this.installed = false;
    }
  
    /**
     * Process console arguments.
     */
    private processArgs(args: unknown[], method: ConsoleMethod): unknown[] | null {
      const processedArgs: unknown[] = [];
      let secretsDetected = false;
      
      for (const arg of args) {
        if (typeof arg === 'string') {
          // Check for secrets
          if (!this.airlock.isSafe(arg)) {
            secretsDetected = true;
            
            if (this.options.blockSecrets) {
              // Don't include the secret, add placeholder
              processedArgs.push('[BLOCKED: Secret detected]');
            } else {
              // Scrub and include
              processedArgs.push(this.airlock.scrub(arg));
            }
          } else {
            processedArgs.push(arg);
          }
        } else if (typeof arg === 'object' && arg !== null) {
          // Deep check object
          const stringified = JSON.stringify(arg);
          if (!this.airlock.isSafe(stringified)) {
            secretsDetected = true;
            
            if (this.options.blockSecrets) {
              processedArgs.push('[BLOCKED: Object contains secrets]');
            } else {
              processedArgs.push(this.airlock.scrubObject(arg as Record<string, unknown>));
            }
          } else {
            processedArgs.push(arg);
          }
        } else {
          processedArgs.push(arg);
        }
      }
      
      if (secretsDetected) {
        this.options.onSecretDetected?.(method, args);
        
        if (this.options.blockSecrets) {
          return processedArgs;
        }
      }
      
      return processedArgs;
    }
  }
  EOF
  ```

- [ ] **3.1.4.2** Create `src/guards/network.ts`
  ```bash
  cat > src/guards/network.ts << 'EOF'
  /**
   * Network Spy - Monitors and reports failed network requests.
   */
  
  import { NetworkEvent } from '../types';
  
  interface NetworkSpyOptions {
    /** Only track requests to these domains */
    allowedDomains?: string[];
    /** Ignore requests to these domains */
    ignoredDomains?: string[];
    /** Callback for failed requests */
    onRequestFailed?: (event: NetworkEvent) => void;
    /** Callback for network errors */
    onNetworkError?: (event: NetworkEvent) => void;
  }
  
  export class NetworkSpy {
    private originalFetch?: typeof fetch;
    private options: NetworkSpyOptions;
    private installed = false;
  
    constructor(options: NetworkSpyOptions = {}) {
      this.options = options;
    }
  
    /**
     * Install network monitoring.
     */
    install(): void {
      if (this.installed || typeof window === 'undefined') return;
      
      this.originalFetch = window.fetch.bind(window);
      
      window.fetch = async (...args: Parameters<typeof fetch>) => {
        const startTime = performance.now();
        const url = this.getUrl(args[0]);
        const method = this.getMethod(args[1]);
        
        // Check if we should track this request
        if (!this.shouldTrack(url)) {
          return this.originalFetch!(...args);
        }
        
        try {
          const response = await this.originalFetch!(...args);
          const duration = performance.now() - startTime;
          
          if (!response.ok) {
            this.options.onRequestFailed?.({
              url,
              method,
              status: response.status,
              statusText: response.statusText,
              duration,
            });
          }
          
          return response;
        } catch (error) {
          const duration = performance.now() - startTime;
          
          this.options.onNetworkError?.({
            url,
            method,
            duration,
            error: error instanceof Error ? error.message : String(error),
          });
          
          throw error;
        }
      };
      
      this.installed = true;
    }
  
    /**
     * Uninstall network monitoring.
     */
    uninstall(): void {
      if (!this.installed || !this.originalFetch) return;
      
      window.fetch = this.originalFetch;
      this.installed = false;
    }
  
    /**
     * Extract URL from fetch input.
     */
    private getUrl(input: RequestInfo | URL): string {
      if (typeof input === 'string') {
        return input;
      } else if (input instanceof URL) {
        return input.toString();
      } else if (input instanceof Request) {
        return input.url;
      }
      return 'unknown';
    }
  
    /**
     * Extract method from fetch options.
     */
    private getMethod(init?: RequestInit): string {
      return init?.method?.toUpperCase() || 'GET';
    }
  
    /**
     * Check if request should be tracked.
     */
    private shouldTrack(url: string): boolean {
      try {
        const urlObj = new URL(url, window.location.origin);
        const domain = urlObj.hostname;
        
        // Check ignored domains
        if (this.options.ignoredDomains?.some((d) => domain.includes(d))) {
          return false;
        }
        
        // Check allowed domains
        if (this.options.allowedDomains?.length) {
          return this.options.allowedDomains.some((d) => domain.includes(d));
        }
        
        return true;
      } catch {
        return true;
      }
    }
  }
  EOF
  ```

- [ ] **3.1.4.3** Create `src/guards/error-boundary.tsx`
  ```bash
  cat > src/guards/error-boundary.tsx << 'EOF'
  /**
   * React Error Boundary for CodeWarden.
   */
  
  import React, { Component, ErrorInfo, ReactNode } from 'react';
  import { ErrorEvent } from '../types';
  
  interface ErrorBoundaryProps {
    /** Children to render */
    children: ReactNode;
    /** Fallback UI when error occurs */
    fallback?: ReactNode | ((error: Error) => ReactNode);
    /** Callback when error is caught */
    onError?: (event: ErrorEvent) => void;
    /** Reset error on prop changes */
    resetKeys?: unknown[];
  }
  
  interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
  }
  
  export class CodeWardenErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
      super(props);
      this.state = { hasError: false, error: null };
    }
  
    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
      return { hasError: true, error };
    }
  
    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
      this.props.onError?.({
        errorType: error.name,
        errorMessage: error.message,
        stackTrace: error.stack,
        componentStack: errorInfo.componentStack || undefined,
      });
    }
  
    componentDidUpdate(prevProps: ErrorBoundaryProps): void {
      // Reset error when resetKeys change
      if (this.state.hasError && this.props.resetKeys) {
        const keysChanged = this.props.resetKeys.some(
          (key, index) => key !== prevProps.resetKeys?.[index]
        );
        
        if (keysChanged) {
          this.setState({ hasError: false, error: null });
        }
      }
    }
  
    render(): ReactNode {
      if (this.state.hasError) {
        const { fallback } = this.props;
        const { error } = this.state;
        
        if (typeof fallback === 'function') {
          return fallback(error!);
        }
        
        if (fallback) {
          return fallback;
        }
        
        return (
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <h2>Something went wrong</h2>
            <p>We&apos;ve been notified and are working on a fix.</p>
            <button onClick={() => this.setState({ hasError: false, error: null })}>
              Try again
            </button>
          </div>
        );
      }
  
      return this.props.children;
    }
  }
  EOF
  ```

- [ ] **3.1.4.4** Create `src/guards/index.ts`
  ```bash
  cat > src/guards/index.ts << 'EOF'
  export { ConsoleGuard } from './console';
  export { NetworkSpy } from './network';
  export { CodeWardenErrorBoundary } from './error-boundary';
  EOF
  ```

---

### Task 3.1.5: Implement Main CodeWarden Class

**Sub-tasks:**

- [ ] **3.1.5.1** Create `src/transport/client.ts`
  ```bash
  mkdir -p src/transport
  
  cat > src/transport/client.ts << 'EOF'
  /**
   * Transport client for CodeWarden API.
   */
  
  import { CodeWardenConfig, TelemetryPayload, TelemetryResponse } from '../types';
  
  export class TransportClient {
    private config: Required<CodeWardenConfig>;
    private queue: TelemetryPayload[] = [];
    private flushTimeout: ReturnType<typeof setTimeout> | null = null;
  
    constructor(config: Required<CodeWardenConfig>) {
      this.config = config;
    }
  
    /**
     * Send telemetry data.
     */
    async send(payload: TelemetryPayload): Promise<TelemetryResponse | null> {
      if (!this.config.enabled || !this.config.apiKey) {
        return null;
      }
  
      try {
        const response = await fetch(`${this.config.apiUrl}/v1/telemetry`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.config.apiKey}`,
            'User-Agent': 'codewarden-js/0.1.0',
          },
          body: JSON.stringify(payload),
        });
  
        if (!response.ok) {
          if (this.config.debug) {
            console.warn(`[CodeWarden] Failed to send telemetry: ${response.status}`);
          }
          return null;
        }
  
        return await response.json();
      } catch (error) {
        if (this.config.debug) {
          console.warn('[CodeWarden] Failed to send telemetry:', error);
        }
        return null;
      }
    }
  
    /**
     * Queue telemetry for batch sending.
     */
    enqueue(payload: TelemetryPayload): void {
      this.queue.push(payload);
      
      // Flush after short delay to batch requests
      if (!this.flushTimeout) {
        this.flushTimeout = setTimeout(() => this.flush(), 1000);
      }
    }
  
    /**
     * Flush queued telemetry.
     */
    async flush(): Promise<void> {
      if (this.flushTimeout) {
        clearTimeout(this.flushTimeout);
        this.flushTimeout = null;
      }
  
      const toSend = [...this.queue];
      this.queue = [];
  
      await Promise.all(toSend.map((payload) => this.send(payload)));
    }
  }
  EOF
  
  cat > src/transport/index.ts << 'EOF'
  export { TransportClient } from './client';
  EOF
  ```

- [ ] **3.1.5.2** Create `src/CodeWarden.ts`
  ```bash
  cat > src/CodeWarden.ts << 'EOF'
  /**
   * CodeWarden JavaScript SDK - Main entry point.
   */
  
  import { CodeWardenConfig, ErrorEvent, NetworkEvent, TelemetryPayload } from './types';
  import { Airlock } from './scrubber';
  import { ConsoleGuard, NetworkSpy } from './guards';
  import { TransportClient } from './transport';
  
  const DEFAULT_CONFIG: Required<CodeWardenConfig> = {
    apiKey: '',
    apiUrl: 'https://api.codewarden.io',
    enabled: true,
    scrubPii: true,
    captureErrors: true,
    captureConsole: true,
    captureNetwork: true,
    environment: 'production',
    debug: false,
  };
  
  export class CodeWarden {
    private config: Required<CodeWardenConfig>;
    private airlock: Airlock;
    private transport: TransportClient;
    private consoleGuard?: ConsoleGuard;
    private networkSpy?: NetworkSpy;
    private initialized = false;
  
    constructor(config: CodeWardenConfig = {}) {
      this.config = { ...DEFAULT_CONFIG, ...config };
      
      // Read API key from environment if not provided
      if (!this.config.apiKey && typeof process !== 'undefined') {
        this.config.apiKey = process.env.CODEWARDEN_API_KEY || '';
      }
      
      this.airlock = new Airlock();
      this.transport = new TransportClient(this.config);
    }
  
    /**
     * Initialize CodeWarden.
     */
    async initialize(): Promise<void> {
      if (this.initialized || !this.config.enabled) return;
  
      // Install console guard
      if (this.config.captureConsole && typeof window !== 'undefined') {
        this.consoleGuard = new ConsoleGuard(this.airlock, {
          onSecretDetected: (method, args) => {
            this.reportEvent({
              type: 'log',
              severity: 'high',
              payload: {
                eventType: 'secret_leak_prevented',
                method,
                message: 'Secret detected in console output',
              },
            });
          },
        });
        this.consoleGuard.install();
      }
  
      // Install network spy
      if (this.config.captureNetwork && typeof window !== 'undefined') {
        this.networkSpy = new NetworkSpy({
          onRequestFailed: (event) => this.reportNetworkError(event),
          onNetworkError: (event) => this.reportNetworkError(event),
        });
        this.networkSpy.install();
      }
  
      // Install global error handler
      if (this.config.captureErrors && typeof window !== 'undefined') {
        window.addEventListener('error', (event) => {
          this.reportError({
            errorType: event.error?.name || 'Error',
            errorMessage: event.message,
            stackTrace: event.error?.stack,
          });
        });
  
        window.addEventListener('unhandledrejection', (event) => {
          const error = event.reason;
          this.reportError({
            errorType: error?.name || 'UnhandledRejection',
            errorMessage: error?.message || String(error),
            stackTrace: error?.stack,
          });
        });
      }
  
      this.initialized = true;
  
      if (this.config.debug) {
        console.log('[CodeWarden] Initialized', {
          environment: this.config.environment,
          captureErrors: this.config.captureErrors,
          captureConsole: this.config.captureConsole,
          captureNetwork: this.config.captureNetwork,
        });
      }
    }
  
    /**
     * Report an error.
     */
    reportError(event: ErrorEvent): void {
      let payload: Record<string, unknown> = { ...event };
  
      // Scrub PII
      if (this.config.scrubPii) {
        payload = this.airlock.scrubObject(payload);
      }
  
      this.reportEvent({
        type: 'crash',
        severity: 'critical',
        payload,
      });
    }
  
    /**
     * Report a network error.
     */
    reportNetworkError(event: NetworkEvent): void {
      let payload: Record<string, unknown> = { ...event };
  
      if (this.config.scrubPii) {
        payload = this.airlock.scrubObject(payload);
      }
  
      this.reportEvent({
        type: 'request',
        severity: event.error ? 'high' : 'medium',
        payload,
      });
    }
  
    /**
     * Report a custom event.
     */
    reportEvent(event: Omit<TelemetryPayload, 'source' | 'environment' | 'timestamp'>): void {
      const payload: TelemetryPayload = {
        source: 'frontend-js',
        environment: this.config.environment,
        timestamp: new Date().toISOString(),
        ...event,
      };
  
      this.transport.enqueue(payload);
    }
  
    /**
     * Get the error boundary component.
     */
    getErrorBoundary() {
      // Dynamic import to avoid React dependency issues
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { CodeWardenErrorBoundary } = require('./guards/error-boundary');
      
      const onError = (event: ErrorEvent) => this.reportError(event);
      
      return (props: { children: React.ReactNode; fallback?: React.ReactNode }) => {
        return React.createElement(CodeWardenErrorBoundary, {
          ...props,
          onError,
        });
      };
    }
  
    /**
     * Shutdown CodeWarden.
     */
    async shutdown(): Promise<void> {
      this.consoleGuard?.uninstall();
      this.networkSpy?.uninstall();
      await this.transport.flush();
    }
  }
  EOF
  ```

- [ ] **3.1.5.3** Create `src/index.ts`
  ```bash
  cat > src/index.ts << 'EOF'
  /**
   * CodeWarden JavaScript SDK
   * 
   * You ship the code. We stand guard.
   */
  
  export { CodeWarden } from './CodeWarden';
  export { Airlock } from './scrubber';
  export { ConsoleGuard, NetworkSpy, CodeWardenErrorBoundary } from './guards';
  export type {
    CodeWardenConfig,
    TelemetryPayload,
    ErrorEvent,
    NetworkEvent,
    ScrubResult,
    TelemetryResponse,
  } from './types';
  EOF
  ```

**Testing:**
- [ ] Run `pnpm build` → Builds successfully
- [ ] Run `pnpm test` → All tests pass
- [ ] Run `pnpm typecheck` → No type errors

---

# Phase 4: Dashboard Development

## Story 4.1: Dashboard Setup

### Task 4.1.1: Initialize Next.js Project

**Sub-tasks:**

- [ ] **4.1.1.1** Create Next.js application
  ```bash
  cd packages/dashboard
  
  # Create Next.js app
  pnpm create next-app . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-git
  ```

- [ ] **4.1.1.2** Install additional dependencies
  ```bash
  pnpm add @tanstack/react-query @supabase/supabase-js lucide-react recharts reactflow clsx tailwind-merge
  pnpm add -D @types/node
  ```

- [ ] **4.1.1.3** Update `package.json` scripts
  ```json
  {
    "scripts": {
      "dev": "next dev",
      "build": "next build",
      "start": "next start",
      "lint": "next lint",
      "test": "vitest run",
      "test:watch": "vitest"
    }
  }
  ```

- [ ] **4.1.1.4** Create environment configuration
  ```bash
  cat > .env.local << 'EOF'
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_SUPABASE_URL=http://localhost:8000
  NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
  EOF
  ```

---

### Task 4.1.2: Create Base Layout

**Sub-tasks:**

- [ ] **4.1.2.1** Create `src/app/layout.tsx`
  ```bash
  cat > src/app/layout.tsx << 'EOF'
  import type { Metadata } from 'next';
  import { Inter } from 'next/font/google';
  import './globals.css';
  import { Providers } from '@/components/providers';
  
  const inter = Inter({ subsets: ['latin'] });
  
  export const metadata: Metadata = {
    title: 'CodeWarden - Security Dashboard',
    description: 'You ship the code. We stand guard.',
  };
  
  export default function RootLayout({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <html lang="en">
        <body className={inter.className}>
          <Providers>{children}</Providers>
        </body>
      </html>
    );
  }
  EOF
  ```

- [ ] **4.1.2.2** Create providers component
  ```bash
  mkdir -p src/components
  
  cat > src/components/providers.tsx << 'EOF'
  'use client';
  
  import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
  import { useState } from 'react';
  
  export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(
      () =>
        new QueryClient({
          defaultOptions: {
            queries: {
              staleTime: 60 * 1000,
              refetchOnWindowFocus: false,
            },
          },
        })
    );
  
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  }
  EOF
  ```

- [ ] **4.1.2.3** Create dashboard layout
  ```bash
  mkdir -p src/app/\(dashboard\)
  
  cat > src/app/\(dashboard\)/layout.tsx << 'EOF'
  import { Sidebar } from '@/components/layout/sidebar';
  import { Header } from '@/components/layout/header';
  import { MobileNav } from '@/components/layout/mobile-nav';
  
  export default function DashboardLayout({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Desktop Sidebar */}
        <Sidebar className="hidden md:flex" />
        
        {/* Main Content */}
        <div className="md:pl-64">
          <Header />
          <main className="p-4 md:p-8 pb-20 md:pb-8">
            {children}
          </main>
        </div>
        
        {/* Mobile Bottom Nav */}
        <MobileNav className="md:hidden" />
      </div>
    );
  }
  EOF
  ```

---

### Task 4.1.3: Create Core Components

**Sub-tasks:**

- [ ] **4.1.3.1** Create Sidebar component
  ```bash
  mkdir -p src/components/layout
  
  cat > src/components/layout/sidebar.tsx << 'EOF'
  'use client';
  
  import Link from 'next/link';
  import { usePathname } from 'next/navigation';
  import { cn } from '@/lib/utils';
  import {
    Home,
    Grid,
    Shield,
    FileCheck,
    Settings,
    LogOut,
  } from 'lucide-react';
  
  const navItems = [
    { href: '/', label: 'Overview', icon: Home },
    { href: '/apps', label: 'Apps', icon: Grid },
    { href: '/security', label: 'Security', icon: Shield },
    { href: '/compliance', label: 'Compliance', icon: FileCheck },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];
  
  interface SidebarProps {
    className?: string;
  }
  
  export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();
  
    return (
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-screen w-64 flex-col border-r bg-white',
          className
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <Shield className="h-8 w-8 text-blue-600" />
          <span className="text-xl font-bold text-slate-900">CodeWarden</span>
        </div>
  
        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
  
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
  
        {/* User section */}
        <div className="border-t p-4">
          <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900">
            <LogOut className="h-5 w-5" />
            Sign out
          </button>
        </div>
      </aside>
    );
  }
  EOF
  ```

- [ ] **4.1.3.2** Create Mobile Navigation
  ```bash
  cat > src/components/layout/mobile-nav.tsx << 'EOF'
  'use client';
  
  import Link from 'next/link';
  import { usePathname } from 'next/navigation';
  import { cn } from '@/lib/utils';
  import { Home, Grid, Shield, Settings } from 'lucide-react';
  
  const navItems = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/apps', label: 'Apps', icon: Grid },
    { href: '/security', label: 'Security', icon: Shield },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];
  
  interface MobileNavProps {
    className?: string;
  }
  
  export function MobileNav({ className }: MobileNavProps) {
    const pathname = usePathname();
  
    return (
      <nav
        className={cn(
          'fixed bottom-0 left-0 right-0 z-50 border-t bg-white',
          className
        )}
      >
        <div className="flex justify-around py-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
  
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex flex-col items-center p-2 rounded-lg transition-colors',
                  isActive ? 'text-blue-600' : 'text-slate-500'
                )}
              >
                <Icon className="h-6 w-6" />
                <span className="text-xs mt-1">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    );
  }
  EOF
  ```

- [ ] **4.1.3.3** Create Header component
  ```bash
  cat > src/components/layout/header.tsx << 'EOF'
  'use client';
  
  import { Bell, Search } from 'lucide-react';
  
  export function Header() {
    return (
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-white px-4 md:px-8">
        {/* Search */}
        <div className="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 md:w-96">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
          />
        </div>
  
        {/* Actions */}
        <div className="flex items-center gap-4">
          <button className="relative rounded-lg p-2 hover:bg-slate-100">
            <Bell className="h-5 w-5 text-slate-600" />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
          </button>
          
          <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium">
            U
          </div>
        </div>
      </header>
    );
  }
  EOF
  ```

- [ ] **4.1.3.4** Create utility functions
  ```bash
  mkdir -p src/lib
  
  cat > src/lib/utils.ts << 'EOF'
  import { type ClassValue, clsx } from 'clsx';
  import { twMerge } from 'tailwind-merge';
  
  export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }
  EOF
  ```

---

### Task 4.1.4: Create Dashboard Pages

**Sub-tasks:**

- [ ] **4.1.4.1** Create Overview page
  ```bash
  cat > src/app/\(dashboard\)/page.tsx << 'EOF'
  import { StatusCard } from '@/components/dashboard/status-card';
  import { RecentErrors } from '@/components/dashboard/recent-errors';
  import { MetricsChart } from '@/components/dashboard/metrics-chart';
  
  export default function DashboardPage() {
    return (
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600">
            Overview of your application security and health.
          </p>
        </div>
  
        {/* Status Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatusCard
            title="System Status"
            value="Healthy"
            status="healthy"
            description="All systems operational"
          />
          <StatusCard
            title="Errors Today"
            value="3"
            status="warning"
            description="2 resolved, 1 active"
          />
          <StatusCard
            title="Security Score"
            value="94%"
            status="healthy"
            description="Last scan: 2h ago"
          />
          <StatusCard
            title="Uptime"
            value="99.9%"
            status="healthy"
            description="Last 30 days"
          />
        </div>
  
        {/* Charts */}
        <div className="grid gap-8 lg:grid-cols-2">
          <MetricsChart />
          <RecentErrors />
        </div>
      </div>
    );
  }
  EOF
  ```

- [ ] **4.1.4.2** Create Status Card component
  ```bash
  mkdir -p src/components/dashboard
  
  cat > src/components/dashboard/status-card.tsx << 'EOF'
  import { cn } from '@/lib/utils';
  import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
  
  interface StatusCardProps {
    title: string;
    value: string;
    status: 'healthy' | 'warning' | 'critical';
    description?: string;
  }
  
  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    critical: {
      icon: XCircle,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
  };
  
  export function StatusCard({ title, value, status, description }: StatusCardProps) {
    const config = statusConfig[status];
    const Icon = config.icon;
  
    return (
      <div className="rounded-xl border bg-white p-6">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-600">{title}</span>
          <div className={cn('rounded-full p-1', config.bg)}>
            <Icon className={cn('h-4 w-4', config.color)} />
          </div>
        </div>
        <div className="mt-2">
          <span className="text-2xl font-bold text-slate-900">{value}</span>
        </div>
        {description && (
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        )}
      </div>
    );
  }
  EOF
  ```

- [ ] **4.1.4.3** Create Recent Errors component
  ```bash
  cat > src/components/dashboard/recent-errors.tsx << 'EOF'
  'use client';
  
  import { AlertTriangle, Clock } from 'lucide-react';
  import { cn } from '@/lib/utils';
  
  interface Error {
    id: string;
    type: string;
    message: string;
    file: string;
    time: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
  }
  
  const mockErrors: Error[] = [
    {
      id: '1',
      type: 'ZeroDivisionError',
      message: 'division by zero',
      file: 'services/pricing.py:45',
      time: '2 min ago',
      severity: 'critical',
    },
    {
      id: '2',
      type: 'TypeError',
      message: "Cannot read property 'map' of undefined",
      file: 'components/List.tsx:23',
      time: '15 min ago',
      severity: 'high',
    },
    {
      id: '3',
      type: 'ValidationError',
      message: 'Invalid email format',
      file: 'api/users.py:89',
      time: '1 hour ago',
      severity: 'medium',
    },
  ];
  
  const severityColors = {
    critical: 'border-l-red-500 bg-red-50',
    high: 'border-l-orange-500 bg-orange-50',
    medium: 'border-l-amber-500 bg-amber-50',
    low: 'border-l-blue-500 bg-blue-50',
  };
  
  export function RecentErrors() {
    return (
      <div className="rounded-xl border bg-white p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Recent Errors</h2>
          <button className="text-sm text-blue-600 hover:text-blue-700">
            View all
          </button>
        </div>
  
        <div className="space-y-3">
          {mockErrors.map((error) => (
            <div
              key={error.id}
              className={cn(
                'rounded-lg border-l-4 p-4',
                severityColors[error.severity]
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-slate-600" />
                  <span className="font-medium text-slate-900">{error.type}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <Clock className="h-3 w-3" />
                  {error.time}
                </div>
              </div>
              <p className="mt-1 text-sm text-slate-600">{error.message}</p>
              <p className="mt-1 text-xs text-slate-400 font-mono">{error.file}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }
  EOF
  ```

- [ ] **4.1.4.4** Create Metrics Chart component
  ```bash
  cat > src/components/dashboard/metrics-chart.tsx << 'EOF'
  'use client';
  
  import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
  } from 'recharts';
  
  const mockData = [
    { time: '00:00', errors: 2, requests: 1200 },
    { time: '04:00', errors: 1, requests: 800 },
    { time: '08:00', errors: 5, requests: 2400 },
    { time: '12:00', errors: 3, requests: 3200 },
    { time: '16:00', errors: 2, requests: 2800 },
    { time: '20:00', errors: 1, requests: 1600 },
  ];
  
  export function MetricsChart() {
    return (
      <div className="rounded-xl border bg-white p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Traffic & Errors</h2>
          <select className="rounded-lg border px-3 py-1 text-sm">
            <option>Last 24 hours</option>
            <option>Last 7 days</option>
            <option>Last 30 days</option>
          </select>
        </div>
  
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="requests"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="errors"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
  
        <div className="mt-4 flex justify-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-500" />
            <span className="text-sm text-slate-600">Requests</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-500" />
            <span className="text-sm text-slate-600">Errors</span>
          </div>
        </div>
      </div>
    );
  }
  EOF
  ```

**Testing:**
- [ ] Run `pnpm dev` → Dashboard loads at localhost:3000
- [ ] Test responsive layout on mobile/desktop
- [ ] Verify all components render correctly

---

# Phase 5: Integration & Testing

## Story 5.1: End-to-End Integration

### Task 5.1.1: Integration Test Setup

**Sub-tasks:**

- [ ] **5.1.1.1** Create integration test configuration
  ```bash
  cd packages/api
  
  cat > tests/integration/conftest.py << 'EOF'
  """Integration test configuration."""
  
  import asyncio
  import pytest
  from httpx import AsyncClient
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
  from sqlalchemy.orm import sessionmaker
  
  from api.main import app
  from api.config import settings
  from api.services.database import Base
  
  
  @pytest.fixture(scope="session")
  def event_loop():
      loop = asyncio.get_event_loop_policy().new_event_loop()
      yield loop
      loop.close()
  
  
  @pytest.fixture(scope="session")
  async def test_db():
      """Create test database."""
      engine = create_async_engine(
          settings.database_url.replace("/postgres", "/postgres_test"),
          echo=False
      )
      
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)
      
      yield engine
      
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.drop_all)
      
      await engine.dispose()
  
  
  @pytest.fixture
  async def client():
      """Create test client."""
      async with AsyncClient(app=app, base_url="http://test") as client:
          yield client
  EOF
  ```

- [ ] **5.1.1.2** Create API integration tests
  ```bash
  cat > tests/integration/test_telemetry.py << 'EOF'
  """Integration tests for telemetry endpoints."""
  
  import pytest
  from httpx import AsyncClient
  
  
  @pytest.mark.asyncio
  async def test_telemetry_endpoint(client: AsyncClient):
      """Test telemetry ingestion."""
      response = await client.post(
          "/v1/telemetry",
          json={
              "source": "backend-python",
              "type": "crash",
              "severity": "critical",
              "environment": "test",
              "payload": {
                  "error_type": "TestError",
                  "error_message": "Test error message",
                  "trace_scrubbed": "Traceback..."
              },
              "timestamp": "2026-01-04T10:00:00Z"
          },
          headers={"Authorization": "Bearer cw_test_xxx"}
      )
      
      assert response.status_code == 201
      data = response.json()
      assert "id" in data
      assert data["status"] == "queued"
  
  
  @pytest.mark.asyncio
  async def test_telemetry_without_auth(client: AsyncClient):
      """Test telemetry requires authentication."""
      response = await client.post(
          "/v1/telemetry",
          json={"type": "crash"}
      )
      
      assert response.status_code == 401
  
  
  @pytest.mark.asyncio
  async def test_evidence_endpoint(client: AsyncClient):
      """Test evidence logging."""
      response = await client.post(
          "/v1/evidence",
          json={
              "type": "AUDIT_DEPLOY",
              "data": {
                  "version": "1.0.0",
                  "commit_hash": "abc123"
              },
              "timestamp": "2026-01-04T10:00:00Z"
          },
          headers={"Authorization": "Bearer cw_test_xxx"}
      )
      
      assert response.status_code == 200
  EOF
  ```

- [ ] **5.1.1.3** Create SDK integration tests
  ```bash
  cd packages/sdk-python
  
  cat > tests/integration/test_sdk_api.py << 'EOF'
  """Integration tests for SDK with API."""
  
  import pytest
  from fastapi import FastAPI
  from fastapi.testclient import TestClient
  
  from codewarden import CodeWarden
  
  
  @pytest.fixture
  def app_with_codewarden():
      """Create FastAPI app with CodeWarden."""
      app = FastAPI()
      
      warden = CodeWarden(
          app,
          api_key="cw_test_xxx",
          api_url="http://localhost:8000",
          environment="test"
      )
      
      @app.get("/")
      def read_root():
          return {"message": "Hello"}
      
      @app.get("/error")
      def raise_error():
          raise ValueError("Test error")
      
      return app
  
  
  def test_middleware_attached(app_with_codewarden):
      """Test middleware is attached to app."""
      assert hasattr(app_with_codewarden.state, "codewarden")
  
  
  def test_error_captured(app_with_codewarden):
      """Test errors are captured."""
      client = TestClient(app_with_codewarden, raise_server_exceptions=False)
      
      response = client.get("/error")
      
      assert response.status_code == 500
      # Error should be captured and sent to API
  EOF
  ```

---

### Task 5.1.2: Full System Test

**Sub-tasks:**

- [ ] **5.1.2.1** Create full system test script
  ```bash
  cat > scripts/test-full-system.sh << 'EOF'
  #!/bin/bash
  set -e
  
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║            CODEWARDEN FULL SYSTEM TEST                        ║"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  echo ""
  
  # Colors
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  NC='\033[0m'
  
  # Start services
  echo "Starting services..."
  docker-compose up -d
  sleep 10
  
  # Run API tests
  echo "Running API tests..."
  cd packages/api
  poetry run pytest tests/ -v
  API_EXIT=$?
  cd ../..
  
  # Run SDK tests
  echo "Running Python SDK tests..."
  cd packages/sdk-python
  poetry run pytest tests/ -v
  SDK_PY_EXIT=$?
  cd ../..
  
  echo "Running JavaScript SDK tests..."
  cd packages/sdk-js
  pnpm test
  SDK_JS_EXIT=$?
  cd ../..
  
  # Run Dashboard tests
  echo "Running Dashboard tests..."
  cd packages/dashboard
  pnpm test
  DASHBOARD_EXIT=$?
  cd ../..
  
  # Summary
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "                         TEST RESULTS"
  echo "═══════════════════════════════════════════════════════════════"
  
  if [ $API_EXIT -eq 0 ]; then
      echo -e "API Tests:        ${GREEN}PASSED${NC}"
  else
      echo -e "API Tests:        ${RED}FAILED${NC}"
  fi
  
  if [ $SDK_PY_EXIT -eq 0 ]; then
      echo -e "Python SDK Tests: ${GREEN}PASSED${NC}"
  else
      echo -e "Python SDK Tests: ${RED}FAILED${NC}"
  fi
  
  if [ $SDK_JS_EXIT -eq 0 ]; then
      echo -e "JS SDK Tests:     ${GREEN}PASSED${NC}"
  else
      echo -e "JS SDK Tests:     ${RED}FAILED${NC}"
  fi
  
  if [ $DASHBOARD_EXIT -eq 0 ]; then
      echo -e "Dashboard Tests:  ${GREEN}PASSED${NC}"
  else
      echo -e "Dashboard Tests:  ${RED}FAILED${NC}"
  fi
  
  # Exit with failure if any test failed
  if [ $API_EXIT -ne 0 ] || [ $SDK_PY_EXIT -ne 0 ] || [ $SDK_JS_EXIT -ne 0 ] || [ $DASHBOARD_EXIT -ne 0 ]; then
      exit 1
  fi
  
  echo ""
  echo -e "${GREEN}All tests passed!${NC}"
  EOF
  
  chmod +x scripts/test-full-system.sh
  ```

---

# Phase 6: Launch Preparation

## Story 6.1: Pre-Launch Checklist

### Task 6.1.1: Package Name Verification

**Sub-tasks:**

- [ ] **6.1.1.1** Check PyPI availability
  ```bash
  pip index versions codewarden
  # If taken, update package name in:
  # - packages/sdk-python/pyproject.toml
  # - All documentation
  # - All code examples
  ```

- [ ] **6.1.1.2** Check NPM availability
  ```bash
  npm view codewarden-js
  # If taken, update package name in:
  # - packages/sdk-js/package.json
  # - All documentation
  # - All code examples
  ```

- [ ] **6.1.1.3** Reserve GitHub organization/repo
  ```
  - [ ] github.com/codewarden
  - [ ] github.com/codewarden/codewarden
  ```

---

### Task 6.1.2: Production Environment Setup

**Sub-tasks:**

- [ ] **6.1.2.1** Configure Supabase production
  ```
  - [ ] Create production project
  - [ ] Configure auth settings
  - [ ] Set up RLS policies
  - [ ] Enable point-in-time recovery
  ```

- [ ] **6.1.2.2** Configure Railway production
  ```
  - [ ] Create production service
  - [ ] Set environment variables
  - [ ] Configure auto-scaling
  - [ ] Set up health checks
  ```

- [ ] **6.1.2.3** Configure Vercel production
  ```
  - [ ] Connect repository
  - [ ] Set environment variables
  - [ ] Configure custom domain
  - [ ] Enable analytics
  ```

- [ ] **6.1.2.4** Configure Cloudflare
  ```
  - [ ] Add DNS records
  - [ ] Enable SSL/TLS
  - [ ] Configure WAF rules
  - [ ] Set up rate limiting
  ```

---

### Task 6.1.3: Documentation Finalization

**Sub-tasks:**

- [ ] **6.1.3.1** Create SDK documentation
  ```bash
  mkdir -p docs/sdk
  
  # Create Python SDK docs
  # Create JavaScript SDK docs
  # Create API reference
  ```

- [ ] **6.1.3.2** Create getting started guide
  ```bash
  mkdir -p docs/getting-started
  
  # Create quickstart.md
  # Create installation.md
  # Create first-alert.md
  ```

- [ ] **6.1.3.3** Create marketing site content
  ```
  - [ ] Homepage copy
  - [ ] Features page
  - [ ] Pricing page
  - [ ] About page
  ```

---

### Task 6.1.4: Launch Day Preparation

**Sub-tasks:**

- [ ] **6.1.4.1** Publish Python SDK
  ```bash
  cd packages/sdk-python
  poetry build
  poetry publish
  ```

- [ ] **6.1.4.2** Publish JavaScript SDK
  ```bash
  cd packages/sdk-js
  pnpm build
  npm publish
  ```

- [ ] **6.1.4.3** Deploy production services
  ```bash
  # Merge to main triggers auto-deployment
  git checkout main
  git merge develop
  git push origin main
  ```

- [ ] **6.1.4.4** Product Hunt preparation
  ```
  - [ ] Create Product Hunt account
  - [ ] Prepare launch assets
  - [ ] Write launch description
  - [ ] Schedule launch date
  ```

---

## Final Checklist

### Code Complete
- [ ] Python SDK fully implemented and tested
- [ ] JavaScript SDK fully implemented and tested
- [ ] API fully implemented and tested
- [ ] Dashboard fully implemented and tested
- [ ] All integrations working

### Infrastructure Ready
- [ ] Production databases configured
- [ ] CDN and WAF configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] SSL certificates configured

### Documentation Complete
- [ ] SDK documentation
- [ ] API documentation
- [ ] Getting started guides
- [ ] Troubleshooting guides

### Marketing Ready
- [ ] Landing page live
- [ ] Product Hunt submission ready
- [ ] Social media accounts set up
- [ ] Email templates created

### Legal & Compliance
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] GDPR compliance verified
- [ ] SOC 2 controls documented

---

## Post-Launch Tasks

- [ ] Monitor error rates
- [ ] Track user signups
- [ ] Respond to feedback
- [ ] Fix reported bugs
- [ ] Plan Phase 2 features

---

**Document Control:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Engineering | Initial release |
