/**
 * Network Spy - Intercepts network requests for monitoring
 *
 * Captures fetch and XMLHttpRequest calls, recording timing,
 * status codes, and errors for observability.
 */

import type { CodeWardenClient } from '../client';

export interface NetworkSpyConfig {
  /** Capture fetch requests (default: true) */
  captureFetch?: boolean;
  /** Capture XMLHttpRequest (default: true) */
  captureXHR?: boolean;
  /** URL patterns to exclude from capture */
  excludeUrls?: (string | RegExp)[];
  /** Include request/response headers (default: false) */
  includeHeaders?: boolean;
  /** Sensitive headers to redact */
  sensitiveHeaders?: string[];
  /** Report failed requests only (default: false) */
  errorsOnly?: boolean;
  /** Minimum duration (ms) to report (default: 0) */
  minDuration?: number;
  /** Report as breadcrumbs instead of events (default: true) */
  asBreadcrumbs?: boolean;
}

interface CapturedRequest {
  url: string;
  method: string;
  startTime: number;
  headers?: Record<string, string>;
}

interface ResponseInfo {
  status: number;
  statusText: string;
  duration: number;
  headers?: Record<string, string>;
  error?: string;
}

export class NetworkSpy {
  private readonly client: CodeWardenClient;
  private readonly config: Required<NetworkSpyConfig>;
  private originalFetch: typeof fetch | null = null;
  private originalXHROpen: typeof XMLHttpRequest.prototype.open | null = null;
  private originalXHRSend: typeof XMLHttpRequest.prototype.send | null = null;
  private installed = false;

  constructor(client: CodeWardenClient, config: NetworkSpyConfig = {}) {
    this.client = client;
    this.config = {
      captureFetch: true,
      captureXHR: true,
      excludeUrls: [],
      includeHeaders: false,
      sensitiveHeaders: [
        'authorization',
        'cookie',
        'x-api-key',
        'x-auth-token',
        'x-csrf-token',
      ],
      errorsOnly: false,
      minDuration: 0,
      asBreadcrumbs: true,
      ...config,
    };
  }

  /**
   * Install the network spy.
   */
  install(): void {
    if (this.installed) {
      return;
    }

    if (this.config.captureFetch && typeof fetch !== 'undefined') {
      this.installFetchInterceptor();
    }

    if (this.config.captureXHR && typeof XMLHttpRequest !== 'undefined') {
      this.installXHRInterceptor();
    }

    this.installed = true;
  }

  /**
   * Uninstall the network spy.
   */
  uninstall(): void {
    if (!this.installed) {
      return;
    }

    // Restore fetch
    if (this.originalFetch && typeof window !== 'undefined') {
      (window as unknown as { fetch: typeof fetch }).fetch = this.originalFetch;
      this.originalFetch = null;
    }

    // Restore XHR
    if (this.originalXHROpen) {
      XMLHttpRequest.prototype.open = this.originalXHROpen;
      this.originalXHROpen = null;
    }

    if (this.originalXHRSend) {
      XMLHttpRequest.prototype.send = this.originalXHRSend;
      this.originalXHRSend = null;
    }

    this.installed = false;
  }

  /**
   * Check if the spy is installed.
   */
  isInstalled(): boolean {
    return this.installed;
  }

  private installFetchInterceptor(): void {
    this.originalFetch = fetch;
    const self = this;

    const interceptedFetch: typeof fetch = async function(
      input: RequestInfo | URL,
      init?: RequestInit
    ): Promise<Response> {
      const url = self.extractUrl(input);
      const method = init?.method || 'GET';

      // Check if should capture
      if (!self.shouldCapture(url)) {
        return self.originalFetch!(input, init);
      }

      const requestInfo: CapturedRequest = {
        url,
        method: method.toUpperCase(),
        startTime: Date.now(),
        headers: self.config.includeHeaders ? self.extractHeaders(init?.headers) : undefined,
      };

      try {
        const response = await self.originalFetch!(input, init);
        const duration = Date.now() - requestInfo.startTime;

        const responseInfo: ResponseInfo = {
          status: response.status,
          statusText: response.statusText,
          duration,
          headers: self.config.includeHeaders ? self.headersToObject(response.headers) : undefined,
        };

        self.report(requestInfo, responseInfo);

        return response;
      } catch (error) {
        const duration = Date.now() - requestInfo.startTime;

        const responseInfo: ResponseInfo = {
          status: 0,
          statusText: 'Network Error',
          duration,
          error: error instanceof Error ? error.message : String(error),
        };

        self.report(requestInfo, responseInfo);

        throw error;
      }
    };

    if (typeof window !== 'undefined') {
      (window as unknown as { fetch: typeof fetch }).fetch = interceptedFetch;
    } else if (typeof globalThis !== 'undefined') {
      (globalThis as unknown as { fetch: typeof fetch }).fetch = interceptedFetch;
    }
  }

  private installXHRInterceptor(): void {
    this.originalXHROpen = XMLHttpRequest.prototype.open;
    this.originalXHRSend = XMLHttpRequest.prototype.send;
    const self = this;

    XMLHttpRequest.prototype.open = function(
      method: string,
      url: string | URL,
      async: boolean = true,
      username?: string | null,
      password?: string | null
    ): void {
      const urlString = typeof url === 'string' ? url : url.toString();

      // Store request info on the XHR object
      (this as XMLHttpRequest & { _cwRequest?: CapturedRequest })._cwRequest = {
        url: urlString,
        method: method.toUpperCase(),
        startTime: 0,
      };

      return self.originalXHROpen!.call(this, method, url, async, username, password);
    };

    XMLHttpRequest.prototype.send = function(body?: Document | XMLHttpRequestBodyInit | null): void {
      const xhr = this as XMLHttpRequest & { _cwRequest?: CapturedRequest };
      const requestInfo = xhr._cwRequest;

      if (!requestInfo || !self.shouldCapture(requestInfo.url)) {
        return self.originalXHRSend!.call(this, body);
      }

      requestInfo.startTime = Date.now();

      const handleComplete = (): void => {
        const duration = Date.now() - requestInfo.startTime;

        const responseInfo: ResponseInfo = {
          status: xhr.status,
          statusText: xhr.statusText || 'Unknown',
          duration,
          error: xhr.status === 0 ? 'Network Error' : undefined,
        };

        self.report(requestInfo, responseInfo);
      };

      xhr.addEventListener('load', handleComplete);
      xhr.addEventListener('error', handleComplete);
      xhr.addEventListener('timeout', () => {
        const duration = Date.now() - requestInfo.startTime;

        const responseInfo: ResponseInfo = {
          status: 0,
          statusText: 'Timeout',
          duration,
          error: 'Request timed out',
        };

        self.report(requestInfo, responseInfo);
      });

      return self.originalXHRSend!.call(this, body);
    };
  }

  private shouldCapture(url: string): boolean {
    // Exclude CodeWarden's own endpoints
    if (url.includes('codewarden.io') || url.includes('ingest.codewarden')) {
      return false;
    }

    // Check exclude patterns
    for (const pattern of this.config.excludeUrls) {
      if (typeof pattern === 'string') {
        if (url.includes(pattern)) {
          return false;
        }
      } else if (pattern instanceof RegExp) {
        if (pattern.test(url)) {
          return false;
        }
      }
    }

    return true;
  }

  private report(request: CapturedRequest, response: ResponseInfo): void {
    // Skip if errors only and no error
    const isError = response.status === 0 || response.status >= 400;
    if (this.config.errorsOnly && !isError) {
      return;
    }

    // Skip if below minimum duration
    if (response.duration < this.config.minDuration) {
      return;
    }

    // Build message
    const message = `${request.method} ${this.truncateUrl(request.url)} - ${response.status} (${response.duration}ms)`;

    if (isError) {
      // Report errors as events
      const errorMessage = response.error
        ? `Network request failed: ${request.method} ${this.truncateUrl(request.url)} - ${response.error}`
        : `HTTP ${response.status}: ${request.method} ${this.truncateUrl(request.url)}`;

      this.client.captureMessage(errorMessage, 'error');
    } else if (!this.config.asBreadcrumbs) {
      // Report as info event
      this.client.captureMessage(message, 'info');
    }
    // If asBreadcrumbs is true and not an error, we would add a breadcrumb
    // This would require extending the client with breadcrumb support
  }

  private extractUrl(input: RequestInfo | URL): string {
    if (typeof input === 'string') {
      return input;
    }

    if (input instanceof URL) {
      return input.toString();
    }

    if (input instanceof Request) {
      return input.url;
    }

    return String(input);
  }

  private extractHeaders(headers?: HeadersInit): Record<string, string> {
    const result: Record<string, string> = {};

    if (!headers) {
      return result;
    }

    if (headers instanceof Headers) {
      headers.forEach((value, key) => {
        result[key] = this.sanitizeHeader(key, value);
      });
    } else if (Array.isArray(headers)) {
      for (const [key, value] of headers) {
        result[key] = this.sanitizeHeader(key, value);
      }
    } else {
      for (const [key, value] of Object.entries(headers)) {
        result[key] = this.sanitizeHeader(key, value);
      }
    }

    return result;
  }

  private headersToObject(headers: Headers): Record<string, string> {
    const result: Record<string, string> = {};
    headers.forEach((value, key) => {
      result[key] = this.sanitizeHeader(key, value);
    });
    return result;
  }

  private sanitizeHeader(key: string, value: string): string {
    const keyLower = key.toLowerCase();

    if (this.config.sensitiveHeaders.some(h => keyLower === h.toLowerCase())) {
      return '[REDACTED]';
    }

    return value;
  }

  private truncateUrl(url: string, maxLength = 100): string {
    if (url.length <= maxLength) {
      return url;
    }

    // Try to keep the host and truncate the path
    try {
      const parsed = new URL(url);
      const host = parsed.host;
      const path = parsed.pathname + parsed.search;

      if (path.length > maxLength - host.length - 10) {
        return `${parsed.protocol}//${host}${path.substring(0, maxLength - host.length - 15)}...`;
      }

      return url;
    } catch {
      return url.substring(0, maxLength) + '...';
    }
  }
}
