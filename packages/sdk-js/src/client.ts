/**
 * CodeWarden Client - Main SDK client class
 */

import { Airlock } from './airlock';
import { Transport } from './transport';
import type { CodeWardenConfig, Event, EventContext, ExceptionInfo, LogLevel, StackFrame } from './types';

function generateEventId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export class CodeWardenClient {
  private readonly config: Omit<Required<Omit<CodeWardenConfig, 'beforeSend' | 'release'>>, never> & { beforeSend?: CodeWardenConfig['beforeSend']; release?: string };
  private readonly transport: Transport;
  private readonly airlock: Airlock | null;
  private context: EventContext = {};

  constructor(config: CodeWardenConfig) {
    this.config = {
      environment: 'production',
      debug: false,
      enablePiiScrubbing: true,
      ...config,
    };

    this.transport = new Transport(this.config.dsn, { debug: this.config.debug });
    this.airlock = this.config.enablePiiScrubbing ? new Airlock() : null;
  }

  /**
   * Set context for future events.
   */
  setContext(context: Partial<EventContext>): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * Set user information for future events.
   */
  setUser(user: { id?: string; email?: string; username?: string }): void {
    if (user.id) this.context.userId = user.id;
  }

  /**
   * Capture an exception.
   */
  captureException(error: Error): string {
    const event = this.buildEvent('error', error.message, error);
    return this.sendEvent(event);
  }

  /**
   * Capture a message.
   */
  captureMessage(message: string, level: LogLevel = 'info'): string {
    const event = this.buildEvent(level, message);
    return this.sendEvent(event);
  }

  private buildEvent(level: LogLevel, message: string, error?: Error): Event {
    let event: Event = {
      eventId: generateEventId(),
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.context },
      tags: {},
      extra: {},
      environment: this.config.environment,
      release: this.config.release,
    };

    if (error) {
      event.exception = this.parseError(error);
    }

    // Scrub PII if enabled
    if (this.airlock) {
      event = this.airlock.scrubEvent(event);
    }

    return event;
  }

  private sendEvent(event: Event): string {
    // Apply beforeSend hook
    if (this.config.beforeSend) {
      const processedEvent = this.config.beforeSend(event);
      if (!processedEvent) {
        return event.eventId;
      }
      event = processedEvent;
    }

    this.transport.send(event);
    return event.eventId;
  }

  private parseError(error: Error): ExceptionInfo {
    const frames = this.parseStackTrace(error.stack);

    return {
      type: error.name,
      value: error.message,
      stacktrace: frames,
    };
  }

  private parseStackTrace(stack?: string): StackFrame[] {
    if (!stack) return [];

    const lines = stack.split('\n').slice(1);
    return lines
      .map((line) => {
        // Handle Chrome/V8 format: "at functionName (file:line:col)"
        const chromeMatch = line.match(/at\s+(.+?)\s+\((.+):(\d+):(\d+)\)/);
        if (chromeMatch) {
          return {
            function: chromeMatch[1] ?? '<anonymous>',
            filename: chromeMatch[2] ?? '<unknown>',
            lineno: parseInt(chromeMatch[3] ?? '0', 10),
            colno: parseInt(chromeMatch[4] ?? '0', 10),
          };
        }

        // Handle Firefox format: "functionName@file:line:col"
        const firefoxMatch = line.match(/(.+?)@(.+):(\d+):(\d+)/);
        if (firefoxMatch) {
          return {
            function: firefoxMatch[1] ?? '<anonymous>',
            filename: firefoxMatch[2] ?? '<unknown>',
            lineno: parseInt(firefoxMatch[3] ?? '0', 10),
            colno: parseInt(firefoxMatch[4] ?? '0', 10),
          };
        }

        return null;
      })
      .filter((frame): frame is StackFrame => frame !== null);
  }

  /**
   * Flush pending events.
   */
  async flush(): Promise<void> {
    await this.transport.flush();
  }

  /**
   * Close the client.
   */
  async close(): Promise<void> {
    await this.transport.flush();
  }
}
