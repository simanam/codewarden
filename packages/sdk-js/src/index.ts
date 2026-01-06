/**
 * CodeWarden JavaScript SDK
 *
 * A drop-in security and observability SDK for JavaScript/TypeScript applications.
 *
 * @example
 * ```ts
 * import { CodeWarden, ConsoleGuard, NetworkSpy } from 'codewarden-js';
 *
 * const client = CodeWarden.init({ dsn: 'https://key@ingest.codewarden.io/123' });
 *
 * // Enable console monitoring
 * const consoleGuard = new ConsoleGuard(client, { captureErrors: true });
 * consoleGuard.install();
 *
 * // Enable network monitoring
 * const networkSpy = new NetworkSpy(client, { errorsOnly: true });
 * networkSpy.install();
 * ```
 */

export { CodeWardenClient } from './client';
export { Airlock } from './airlock';
export { ConsoleGuard, NetworkSpy } from './guards';
export type { ConsoleGuardConfig, NetworkSpyConfig } from './guards';
export type {
  CodeWardenConfig,
  Event,
  EventContext,
  ExceptionInfo,
  StackFrame,
  LogLevel,
} from './types';

import { CodeWardenClient } from './client';
import type { CodeWardenConfig } from './types';

let globalClient: CodeWardenClient | null = null;

/**
 * CodeWarden SDK facade for easy initialization and usage.
 */
export const CodeWarden = {
  /**
   * Initialize the CodeWarden SDK.
   */
  init(config: CodeWardenConfig): CodeWardenClient {
    globalClient = new CodeWardenClient(config);
    return globalClient;
  },

  /**
   * Get the initialized client instance.
   */
  getClient(): CodeWardenClient {
    if (!globalClient) {
      throw new Error('CodeWarden SDK not initialized. Call CodeWarden.init() first.');
    }
    return globalClient;
  },

  /**
   * Capture an exception.
   */
  captureException(error: Error): string {
    return this.getClient().captureException(error);
  },

  /**
   * Capture a message.
   */
  captureMessage(message: string, level: 'error' | 'warning' | 'info' | 'debug' = 'info'): string {
    return this.getClient().captureMessage(message, level);
  },

  /**
   * Set context for future events.
   */
  setContext(context: Record<string, unknown>): void {
    this.getClient().setContext(context);
  },

  /**
   * Close the SDK and flush pending events.
   */
  async close(): Promise<void> {
    if (globalClient) {
      await globalClient.close();
      globalClient = null;
    }
  },
};
