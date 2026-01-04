/**
 * CodeWarden Airlock - PII Scrubbing Engine
 */

import type { Event } from './types';

interface PatternConfig {
  pattern: RegExp;
  mask: string;
}

const DEFAULT_PATTERNS: Record<string, PatternConfig> = {
  email: {
    pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
    mask: '[EMAIL]',
  },
  phoneUs: {
    pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
    mask: '[PHONE]',
  },
  phoneIntl: {
    pattern: /\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}/g,
    mask: '[PHONE]',
  },
  ssn: {
    pattern: /\b\d{3}-\d{2}-\d{4}\b/g,
    mask: '[SSN]',
  },
  creditCard: {
    pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g,
    mask: '[CARD]',
  },
  ipAddress: {
    pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
    mask: '[IP]',
  },
  apiKey: {
    pattern: /\b(sk|pk|api|key|token|secret|password)[-_]?[A-Za-z0-9]{16,}\b/gi,
    mask: '[REDACTED]',
  },
};

export class Airlock {
  private patterns: Record<string, PatternConfig>;

  constructor(options?: { additionalPatterns?: Record<string, PatternConfig>; enabledPatterns?: string[] }) {
    this.patterns = { ...DEFAULT_PATTERNS };

    if (options?.additionalPatterns) {
      Object.assign(this.patterns, options.additionalPatterns);
    }

    if (options?.enabledPatterns) {
      const filtered: Record<string, PatternConfig> = {};
      for (const key of options.enabledPatterns) {
        if (this.patterns[key]) {
          filtered[key] = this.patterns[key];
        }
      }
      this.patterns = filtered;
    }
  }

  /**
   * Scrub PII from a string.
   */
  scrub(text: string): string {
    let result = text;
    for (const { pattern, mask } of Object.values(this.patterns)) {
      result = result.replace(pattern, mask);
    }
    return result;
  }

  /**
   * Recursively scrub PII from an object.
   */
  scrubObject<T extends Record<string, unknown>>(obj: T): T {
    const result: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string') {
        result[key] = this.scrub(value);
      } else if (Array.isArray(value)) {
        result[key] = value.map((item) => (typeof item === 'string' ? this.scrub(item) : item));
      } else if (value !== null && typeof value === 'object') {
        result[key] = this.scrubObject(value as Record<string, unknown>);
      } else {
        result[key] = value;
      }
    }

    return result as T;
  }

  /**
   * Scrub PII from an event.
   */
  scrubEvent(event: Event): Event {
    const scrubbed = { ...event };

    // Scrub message
    if (scrubbed.message) {
      scrubbed.message = this.scrub(scrubbed.message);
    }

    // Scrub exception value
    if (scrubbed.exception) {
      scrubbed.exception = {
        ...scrubbed.exception,
        value: this.scrub(scrubbed.exception.value),
      };
    }

    // Scrub context
    if (scrubbed.context) {
      scrubbed.context = this.scrubObject(scrubbed.context);
    }

    // Scrub extra
    if (scrubbed.extra) {
      scrubbed.extra = this.scrubObject(scrubbed.extra);
    }

    return scrubbed;
  }
}
