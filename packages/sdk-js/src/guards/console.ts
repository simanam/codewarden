/**
 * Console Guard - Intercepts console methods for error monitoring
 *
 * Captures console.error, console.warn, and optionally console.log/debug
 * calls and reports them to CodeWarden.
 */

import type { CodeWardenClient } from '../client';

export interface ConsoleGuardConfig {
  /** Capture console.error calls (default: true) */
  captureErrors?: boolean;
  /** Capture console.warn calls (default: true) */
  captureWarnings?: boolean;
  /** Capture console.log calls (default: false) */
  captureLogs?: boolean;
  /** Capture console.debug calls (default: false) */
  captureDebug?: boolean;
  /** Patterns to exclude from capture */
  excludePatterns?: (string | RegExp)[];
  /** Maximum arguments to capture per call */
  maxArgs?: number;
  /** Whether to continue logging to original console (default: true) */
  passthrough?: boolean;
}

type ConsoleMethod = 'log' | 'warn' | 'error' | 'debug' | 'info';

interface OriginalMethods {
  log: typeof console.log;
  warn: typeof console.warn;
  error: typeof console.error;
  debug: typeof console.debug;
  info: typeof console.info;
}

export class ConsoleGuard {
  private readonly client: CodeWardenClient;
  private readonly config: Required<ConsoleGuardConfig>;
  private originalMethods: OriginalMethods | null = null;
  private installed = false;
  private callDepth = 0; // Prevent infinite recursion

  constructor(client: CodeWardenClient, config: ConsoleGuardConfig = {}) {
    this.client = client;
    this.config = {
      captureErrors: true,
      captureWarnings: true,
      captureLogs: false,
      captureDebug: false,
      excludePatterns: [],
      maxArgs: 10,
      passthrough: true,
      ...config,
    };
  }

  /**
   * Install the console guard, intercepting console methods.
   */
  install(): void {
    if (this.installed || typeof console === 'undefined') {
      return;
    }

    // Store original methods
    this.originalMethods = {
      log: console.log.bind(console),
      warn: console.warn.bind(console),
      error: console.error.bind(console),
      debug: console.debug.bind(console),
      info: console.info.bind(console),
    };

    // Install interceptors
    if (this.config.captureErrors) {
      console.error = this.createInterceptor('error');
    }

    if (this.config.captureWarnings) {
      console.warn = this.createInterceptor('warn');
    }

    if (this.config.captureLogs) {
      console.log = this.createInterceptor('log');
      console.info = this.createInterceptor('info');
    }

    if (this.config.captureDebug) {
      console.debug = this.createInterceptor('debug');
    }

    this.installed = true;
  }

  /**
   * Uninstall the console guard, restoring original methods.
   */
  uninstall(): void {
    if (!this.installed || !this.originalMethods) {
      return;
    }

    console.log = this.originalMethods.log;
    console.warn = this.originalMethods.warn;
    console.error = this.originalMethods.error;
    console.debug = this.originalMethods.debug;
    console.info = this.originalMethods.info;

    this.originalMethods = null;
    this.installed = false;
  }

  /**
   * Check if the guard is currently installed.
   */
  isInstalled(): boolean {
    return this.installed;
  }

  private createInterceptor(method: ConsoleMethod): (...args: unknown[]) => void {
    const original = this.originalMethods?.[method];

    return (...args: unknown[]): void => {
      // Prevent infinite recursion
      if (this.callDepth > 0) {
        original?.(...args);
        return;
      }

      // Passthrough to original console
      if (this.config.passthrough && original) {
        original(...args);
      }

      // Check if should capture
      if (!this.shouldCapture(args)) {
        return;
      }

      // Capture and report
      this.callDepth++;
      try {
        this.capture(method, args);
      } finally {
        this.callDepth--;
      }
    };
  }

  private shouldCapture(args: unknown[]): boolean {
    if (args.length === 0) {
      return false;
    }

    // Convert first arg to string for pattern matching
    const firstArg = this.safeStringify(args[0]);

    // Check exclude patterns
    for (const pattern of this.config.excludePatterns) {
      if (typeof pattern === 'string') {
        if (firstArg.includes(pattern)) {
          return false;
        }
      } else if (pattern instanceof RegExp) {
        if (pattern.test(firstArg)) {
          return false;
        }
      }
    }

    return true;
  }

  private capture(method: ConsoleMethod, args: unknown[]): void {
    // Limit number of args
    const capturedArgs = args.slice(0, this.config.maxArgs);

    // Build message
    const message = capturedArgs.map(arg => this.safeStringify(arg)).join(' ');

    // Map console method to log level
    const levelMap: Record<ConsoleMethod, 'error' | 'warning' | 'info' | 'debug'> = {
      error: 'error',
      warn: 'warning',
      log: 'info',
      info: 'info',
      debug: 'debug',
    };

    const level = levelMap[method];

    // Check if first arg is an Error object
    const firstArg = args[0];
    if (firstArg instanceof Error) {
      this.client.captureException(firstArg);
    } else {
      this.client.captureMessage(`[console.${method}] ${message}`, level);
    }
  }

  private safeStringify(value: unknown, depth = 0): string {
    if (depth > 3) {
      return '[Max depth]';
    }

    if (value === null) {
      return 'null';
    }

    if (value === undefined) {
      return 'undefined';
    }

    if (typeof value === 'string') {
      return value;
    }

    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }

    if (value instanceof Error) {
      return `${value.name}: ${value.message}`;
    }

    if (typeof value === 'function') {
      return `[Function: ${value.name || 'anonymous'}]`;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return '[]';
      }
      const items = value.slice(0, 5).map(v => this.safeStringify(v, depth + 1));
      if (value.length > 5) {
        items.push(`...+${value.length - 5} more`);
      }
      return `[${items.join(', ')}]`;
    }

    if (typeof value === 'object') {
      try {
        const str = JSON.stringify(value, null, 0);
        if (str.length > 500) {
          return str.substring(0, 500) + '...';
        }
        return str;
      } catch {
        return '[Object]';
      }
    }

    return String(value);
  }
}
