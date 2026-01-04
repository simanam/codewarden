/**
 * CodeWarden Transport - HTTP transport layer
 */

import type { Event } from './types';

interface TransportOptions {
  maxQueueSize?: number;
  batchSize?: number;
  flushInterval?: number;
  timeout?: number;
  maxRetries?: number;
  debug?: boolean;
}

export class Transport {
  private readonly dsn: string;
  private readonly options: Required<TransportOptions>;
  private queue: Event[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(dsn: string, options: TransportOptions = {}) {
    this.dsn = dsn;
    this.options = {
      maxQueueSize: options.maxQueueSize ?? 100,
      batchSize: options.batchSize ?? 10,
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

    if (this.queue.length >= this.options.batchSize) {
      void this.flush();
    }
  }

  /**
   * Flush all pending events.
   */
  async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const events = this.queue.splice(0, this.options.batchSize);
    await this.sendBatch(events);
  }

  private async sendBatch(events: Event[]): Promise<void> {
    for (let attempt = 0; attempt < this.options.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);

        const response = await fetch(this.dsn, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ events }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          if (this.options.debug) {
            console.debug(`[CodeWarden] Sent ${events.length} events successfully`);
          }
          return;
        }

        if (response.status < 500) {
          // Client error, don't retry
          console.error(`[CodeWarden] Failed to send events: ${response.status}`);
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

    console.error(`[CodeWarden] Failed to send ${events.length} events after ${this.options.maxRetries} attempts`);
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
