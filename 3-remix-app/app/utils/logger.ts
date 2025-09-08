/**
 * Enterprise Logger for Remix application
 *
 * Provides structured JSON logging with automatic serialization of complex objects.
 *
 * USAGE EXAMPLES:
 *
 * Basic logging:
 *   import { createLogger } from '~/utils/logger';
 *
 *   export async function loader() {
 *     const logger = createLogger();
 *     logger.info('Processing request', {
 *       userId: '123',
 *       timestamp: new Date(),
 *       error: new Error('Something went wrong'),
 *       metadata: { nested: 'object' }
 *     });
 *   }
 *
 * Service with dependency injection:
 *   class MyService {
 *     constructor(private logger = LoggerFactory.createLogger({ service: 'my-service' })) {}
 *   }
 *
 * Testing:
 *   const mockLogger: Logger = {
 *     error: jest.fn(), warn: jest.fn(),
 *     info: jest.fn(), debug: jest.fn(),
 *   };
 */
import pino from 'pino';
import { getClientEnv } from './env';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';
export type LogValue =
  | string
  | number
  | boolean
  | undefined
  | Date
  | Error
  | object
  | null;
export type LogData = Record<string, LogValue | LogValue[]>;

export interface Logger {
  debug(message: string, data?: LogData): void;
  info(message: string, data?: LogData): void;
  warn(message: string, data?: LogData): void;
  error(message: string, data?: LogData): void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function serializeValue(value: LogValue | LogValue[]): any {
  if (Array.isArray(value)) {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    return value.map((v) => serializeValue(v));
  }
  if (value instanceof Date) return value.toISOString();
  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack,
    };
  }
  if (value && typeof value === 'object') {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const serialized: Record<string, any> = {};
    for (const [key, val] of Object.entries(value)) {
      serialized[key] = serializeValue(val as LogValue);
    }
    return serialized;
  }
  return value;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function serializeData(data?: LogData): Record<string, any> {
  if (!data) return {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const serialized: Record<string, any> = {};
  for (const [key, value] of Object.entries(data)) {
    serialized[key] = serializeValue(value);
  }
  return serialized;
}

/**
 * Main factory for creating logger instances
 */
export class LoggerFactory {
  private static instance: Logger | null = null;

  /**
   * Create a logger with optional default data
   * @param defaultData - Data to include with every log
   * @returns Logger instance
   */
  static createLogger(defaultData?: LogData): Logger {
    if (!this.instance) {
      const pinoLogger = pino({
        level: process.env.LOG_LEVEL || 'info',
        formatters: {
          level: (label) => ({ level: label }),
        },
      });

      this.instance = {
        debug: (message: string, data?: LogData) =>
          pinoLogger.debug({ ...serializeData(defaultData), ...serializeData(data) }, message),
        info: (message: string, data?: LogData) =>
          pinoLogger.info({ ...serializeData(defaultData), ...serializeData(data) }, message),
        warn: (message: string, data?: LogData) =>
          pinoLogger.warn({ ...serializeData(defaultData), ...serializeData(data) }, message),
        error: (message: string, data?: LogData) =>
          pinoLogger.error({ ...serializeData(defaultData), ...serializeData(data) }, message),
      };
    }
    return this.instance;
  }
}

/**
 * Create a basic logger instance
 * @returns Logger instance
 */
export function createLogger(): Logger {
  const env = getClientEnv();
  return LoggerFactory.createLogger({
    app: env.APP_NAME,
    environment: process.env.NODE_ENV || 'development',
  });
}

// Singleton for direct usage
export const logger = createLogger();