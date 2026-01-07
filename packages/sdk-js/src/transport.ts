/**
 * CodeWarden Transport - HTTP transport layer
 */

import type { Event } from './types';

interface TransportOptions {
  maxQueueSize?: number;
  flushInterval?: number;
  timeout?: number;
  maxRetries?: number;
  debug?: boolean;
}

interface TelemetryPayload {
  source: string;
  type: string;
  severity: string;
  environment: string;
  payload: Record<string, unknown>;
  timestamp?: string;
  trace_id?: string;
}

/**
 * Parse a CodeWarden DSN into base URL and API key.
 *
 * DSN format: https://API_KEY@host or https://API_KEY@host:port
 *
 * @example
 * parseDsn('https://cw_live_abc123@api.codewarden.io')
 * // Returns: { baseUrl: 'https://api.codewarden.io', apiKey: 'cw_live_abc123' }
 */
function parseDsn(dsn: string): { baseUrl: string; apiKey: string } {
  if (!dsn) {
    throw new Error('CodeWarden DSN cannot be empty');
  }

  try {
    const url = new URL(dsn);
    const apiKey = url.username || '';

    // Rebuild URL without credentials
    const baseUrl = `${url.protocol}//${url.host}`;

    return { baseUrl, apiKey };
  } catch {
    throw new Error(`Invalid CodeWarden DSN format: ${dsn}`);
  }
}

export class Transport {
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly options: Required<Omit<TransportOptions, 'batchSize'>>;
  private queue: Event[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(dsn: string, options: TransportOptions = {}) {
    const { baseUrl, apiKey } = parseDsn(dsn);
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;

    this.options = {
      maxQueueSize: options.maxQueueSize ?? 100,
      flushInterval: options.flushInterval ?? 5000,
      timeout: options.timeout ?? 30000,
      maxRetries: options.maxRetries ?? 3,
      debug: options.debug ?? false,
    };

    this.startFlushTimer();
  }

  /**
   * Queue an event for sending.
   */
  send(event: Event): void {
    if (this.queue.length >= this.options.maxQueueSize) {
      if (this.options.debug) {
        console.warn('[CodeWarden] Event queue full, dropping event');
      }
      return;
    }

    this.queue.push(event);
    // Send immediately instead of batching
    void this.flush();
  }

  /**
   * Flush all pending events.
   */
  async flush(): Promise<void> {
    while (this.queue.length > 0) {
      const event = this.queue.shift();
      if (event) {
        await this.sendEvent(event);
      }
    }
  }

  /**
   * Transform SDK Event to API TelemetryPayload format.
   */
  private transformEventToPayload(event: Event): TelemetryPayload {
    // Map SDK level to API type/severity
    const level = event.level;
    const eventType = level === 'error' || level === 'warning' ? 'error' : 'info';
    const severityMap: Record<string, string> = {
      error: 'high',
      warning: 'medium',
      info: 'low',
      debug: 'info',
    };
    const severity = severityMap[level] || 'medium';

    // Build payload with exception details
    const payload: Record<string, unknown> = {
      message: event.message,
    };

    const exception = event.exception;
    if (exception) {
      payload.error_type = exception.type;
      payload.error_message = exception.value;

      // Extract file and line from stack trace
      const stacktrace = exception.stacktrace || [];
      if (stacktrace.length > 0) {
        const lastFrame = stacktrace[stacktrace.length - 1];
        payload.file = lastFrame.filename;
        payload.line = lastFrame.lineno;

        // Build full stack trace string
        const traceLines: string[] = [];
        for (const frame of stacktrace) {
          traceLines.push(
            `  at ${frame.function} (${frame.filename}:${frame.lineno}:${frame.colno})`
          );
          if (frame.contextLine) {
            traceLines.push(`    ${frame.contextLine}`);
          }
        }
        payload.stack_trace = traceLines.join('\n');
      }
    }

    // Add context data
    if (event.context && Object.keys(event.context).length > 0) {
      payload.context = event.context;
    }

    // Add tags and extra data
    if (event.tags && Object.keys(event.tags).length > 0) {
      payload.tags = event.tags;
    }
    if (event.extra && Object.keys(event.extra).length > 0) {
      payload.extra = event.extra;
    }

    return {
      source: 'sdk-js',
      type: eventType,
      severity,
      environment: event.environment,
      payload,
      timestamp: event.timestamp,
      trace_id: event.eventId,
    };
  }

  /**
   * Send a single event with retry logic.
   */
  private async sendEvent(event: Event): Promise<void> {
    const payload = this.transformEventToPayload(event);
    const endpoint = `${this.baseUrl}/v1/telemetry`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add API key authorization if present
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    for (let attempt = 0; attempt < this.options.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);

        const response = await fetch(endpoint, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          if (this.options.debug) {
            console.debug(`[CodeWarden] Sent event ${event.eventId} successfully`);
          }
          return;
        }

        if (response.status < 500) {
          // Client error, don't retry
          const text = await response.text();
          console.error(`[CodeWarden] Failed to send event: ${response.status} - ${text}`);
          return;
        }

        // Server error, retry
        if (this.options.debug) {
          console.warn(`[CodeWarden] Server error (attempt ${attempt + 1}): ${response.status}`);
        }
      } catch (error) {
        if (this.options.debug) {
          console.warn(`[CodeWarden] Request error (attempt ${attempt + 1}):`, error);
        }
      }

      // Wait before retry with exponential backoff
      await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }

    console.error(
      `[CodeWarden] Failed to send event ${event.eventId} after ${this.options.maxRetries} attempts`
    );
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      void this.flush();
    }, this.options.flushInterval);
  }

  /**
   * Stop the transport.
   */
  stop(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }
}
