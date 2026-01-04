/**
 * CodeWarden SDK Type Definitions
 */

export type LogLevel = 'error' | 'warning' | 'info' | 'debug';

export interface CodeWardenConfig {
  /** Your CodeWarden DSN (from dashboard) */
  dsn: string;
  /** Environment name (e.g., "production", "staging") */
  environment?: string;
  /** Release/version identifier */
  release?: string;
  /** Enable debug logging */
  debug?: boolean;
  /** Enable automatic PII scrubbing */
  enablePiiScrubbing?: boolean;
  /** Hook called before sending events */
  beforeSend?: (event: Event) => Event | null;
}

export interface EventContext {
  userId?: string;
  sessionId?: string;
  requestId?: string;
  url?: string;
  userAgent?: string;
  [key: string]: unknown;
}

export interface StackFrame {
  filename: string;
  lineno: number;
  colno: number;
  function: string;
  contextLine?: string;
}

export interface ExceptionInfo {
  type: string;
  value: string;
  stacktrace: StackFrame[];
}

export interface Event {
  eventId: string;
  timestamp: string;
  level: LogLevel;
  message?: string;
  exception?: ExceptionInfo;
  context: EventContext;
  tags: Record<string, string>;
  extra: Record<string, unknown>;
  environment: string;
  release?: string;
}
