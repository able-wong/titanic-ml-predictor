import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { getClientEnv, getServerEnv } from '../../utils/env';

describe('Environment Utilities', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    // Reset environment for each test
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // Restore original environment
    process.env = originalEnv;
  });

  describe('getClientEnv', () => {
    it('should return default APP_NAME when not set', () => {
      delete process.env.APP_NAME;
      const env = getClientEnv();
      expect(env.APP_NAME).toBe('Titanic ML Predictor');
    });

    it('should return custom APP_NAME when set', () => {
      process.env.APP_NAME = 'Custom App';
      const env = getClientEnv();
      expect(env.APP_NAME).toBe('Custom App');
    });

    it('should parse valid FIREBASE_CONFIG JSON', () => {
      const firebaseConfig = {
        apiKey: 'test-key',
        authDomain: 'test.firebaseapp.com',
        projectId: 'test-project',
      };
      process.env.FIREBASE_CONFIG = JSON.stringify(firebaseConfig);
      const env = getClientEnv();
      expect(env.FIREBASE_CONFIG).toEqual(firebaseConfig);
    });

    it('should handle invalid FIREBASE_CONFIG JSON gracefully', () => {
      process.env.FIREBASE_CONFIG = 'invalid-json';
      const env = getClientEnv();
      expect(env.FIREBASE_CONFIG).toBeUndefined();
    });

    it('should handle missing FIREBASE_CONFIG', () => {
      delete process.env.FIREBASE_CONFIG;
      const env = getClientEnv();
      expect(env.FIREBASE_CONFIG).toBeUndefined();
    });
  });

  describe('getServerEnv', () => {
    it('should return default ML_SERVICE_URL when not set', () => {
      delete process.env.ML_SERVICE_URL;
      const env = getServerEnv();
      expect(env.ML_SERVICE_URL).toBe('http://localhost:8000');
    });

    it('should return custom ML_SERVICE_URL when set', () => {
      process.env.ML_SERVICE_URL = 'https://api.example.com';
      const env = getServerEnv();
      expect(env.ML_SERVICE_URL).toBe('https://api.example.com');
    });

    it('should include JWT_PRIVATE_KEY when set', () => {
      process.env.JWT_PRIVATE_KEY = 'test-private-key';
      const env = getServerEnv();
      expect(env.JWT_PRIVATE_KEY).toBe('test-private-key');
    });

    it('should handle missing JWT_PRIVATE_KEY', () => {
      delete process.env.JWT_PRIVATE_KEY;
      const env = getServerEnv();
      expect(env.JWT_PRIVATE_KEY).toBeUndefined();
    });

    it('should include all server environment variables', () => {
      process.env.FIREBASE_CONFIG = '{"test": "config"}';
      process.env.FIREBASE_PROJECT_ID = 'test-project';
      process.env.FIREBASE_SERVICE_ACCOUNT_KEY = 'test-key';
      process.env.GOOGLE_GENERATIVE_AI_API_KEY = 'ai-key';
      process.env.GOOGLE_GENERATIVE_AI_MODEL_NAME = 'gemini';
      process.env.JWT_PRIVATE_KEY = 'jwt-key';
      process.env.ML_SERVICE_URL = 'https://ml.example.com';

      const env = getServerEnv();
      
      expect(env.FIREBASE_CONFIG).toBe('{"test": "config"}');
      expect(env.FIREBASE_PROJECT_ID).toBe('test-project');
      expect(env.FIREBASE_SERVICE_ACCOUNT_KEY).toBe('test-key');
      expect(env.GOOGLE_GENERATIVE_AI_API_KEY).toBe('ai-key');
      expect(env.GOOGLE_GENERATIVE_AI_MODEL_NAME).toBe('gemini');
      expect(env.JWT_PRIVATE_KEY).toBe('jwt-key');
      expect(env.ML_SERVICE_URL).toBe('https://ml.example.com');
    });
  });
});