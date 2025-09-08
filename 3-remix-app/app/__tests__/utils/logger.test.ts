import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { LoggerFactory, createLogger } from '../../utils/logger';

// Mock pino
jest.mock('pino', () => {
  return jest.fn(() => ({
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  }));
});

describe('Logger Utilities', () => {
  beforeEach(() => {
    // Clear the logger instance cache
    // @ts-expect-error - accessing private property for testing
    LoggerFactory.instance = null;
    
    // Reset all mocks
    jest.clearAllMocks();
  });

  describe('createLogger', () => {
    it('should create a logger instance', () => {
      const logger = createLogger();
      expect(logger).toBeDefined();
      expect(typeof logger.debug).toBe('function');
      expect(typeof logger.info).toBe('function');
      expect(typeof logger.warn).toBe('function');
      expect(typeof logger.error).toBe('function');
    });

    it('should be callable without errors', () => {
      const logger = createLogger();
      
      expect(() => {
        logger.debug('Debug message');
        logger.info('Info message');
        logger.warn('Warning message');
        logger.error('Error message');
      }).not.toThrow();
    });

    it('should handle data objects', () => {
      const logger = createLogger();
      
      expect(() => {
        logger.info('Test message', {
          string: 'value',
          number: 123,
          boolean: true,
          date: new Date(),
          error: new Error('Test error'),
          nested: {
            key: 'value',
          },
          array: [1, 2, 3],
        });
      }).not.toThrow();
    });
  });

  describe('LoggerFactory', () => {
    it('should create logger with default data', () => {
      const logger = LoggerFactory.createLogger({
        service: 'test-service',
        version: '1.0.0',
      });
      
      expect(logger).toBeDefined();
      expect(() => {
        logger.info('Factory logger message');
      }).not.toThrow();
    });

    it('should return the same instance on multiple calls', () => {
      const logger1 = LoggerFactory.createLogger();
      const logger2 = LoggerFactory.createLogger();
      
      expect(logger1).toBe(logger2);
    });
  });
});