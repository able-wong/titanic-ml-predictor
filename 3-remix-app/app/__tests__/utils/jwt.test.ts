import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { decodeToken, isTokenExpired } from '../../utils/jwt';

// Mock the env module
jest.mock('../../utils/env', () => ({
  getServerEnv: jest.fn(() => ({
    JWT_PRIVATE_KEY: 'test-private-key',
    ML_SERVICE_URL: 'http://localhost:8000',
  })),
}));

describe('JWT Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Token Decoding (without verification)', () => {
    it('should return null for malformed tokens', () => {
      const malformed = 'not.a.valid.jwt';
      const decoded = decodeToken(malformed);
      expect(decoded).toBeNull();
    });

    it('should return null for invalid base64', () => {
      const invalid = 'invalid.invalid.invalid';
      const decoded = decodeToken(invalid);
      expect(decoded).toBeNull();
    });

    it('should decode a properly formatted JWT token', () => {
      // Create a test JWT token manually (header.payload.signature)
      const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({ 
        user_id: 'test123', 
        username: 'testuser',
        exp: Math.floor(Date.now() / 1000) + 3600 
      }));
      const signature = 'test-signature';
      const testToken = `${header}.${payload}.${signature}`;

      const decoded = decodeToken(testToken);
      expect(decoded).toBeDefined();
      expect(decoded?.user_id).toBe('test123');
      expect(decoded?.username).toBe('testuser');
    });
  });

  describe('Token Expiration', () => {
    it('should detect expired tokens', () => {
      // Create a token with past expiration
      const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({ 
        user_id: 'test123',
        exp: Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
      }));
      const signature = 'test-signature';
      const expiredToken = `${header}.${payload}.${signature}`;

      const isExpired = isTokenExpired(expiredToken);
      expect(isExpired).toBe(true);
    });

    it('should detect valid tokens', () => {
      // Create a token with future expiration
      const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({ 
        user_id: 'test123',
        exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
      }));
      const signature = 'test-signature';
      const validToken = `${header}.${payload}.${signature}`;

      const isExpired = isTokenExpired(validToken);
      expect(isExpired).toBe(false);
    });

    it('should return true for malformed tokens', () => {
      const malformed = 'not.a.valid.jwt';
      const isExpired = isTokenExpired(malformed);
      
      expect(isExpired).toBe(true);
    });
  });

  describe('Environment Variables', () => {
    it('should access environment variables through getServerEnv', () => {
      const { getServerEnv } = require('../../utils/env');
      const env = getServerEnv();
      
      expect(env).toBeDefined();
      expect(env.JWT_PRIVATE_KEY).toBe('test-private-key');
      expect(env.ML_SERVICE_URL).toBe('http://localhost:8000');
    });
  });
});