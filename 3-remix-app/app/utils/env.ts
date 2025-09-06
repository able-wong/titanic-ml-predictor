/**
 * Environment variables configuration
 * Handles both client and server environment variables
 */

import type { FirebaseConfig } from '~/interfaces/firebaseInterface';

// Frontend environment variables (safe to expose)
export interface ClientEnv {
  FIREBASE_CONFIG?: FirebaseConfig;
  APP_NAME: string;
}

// Server-side environment variables
export interface ServerEnv {
  FIREBASE_CONFIG?: string;
  FIREBASE_PROJECT_ID?: string;
  FIREBASE_SERVICE_ACCOUNT_KEY?: string;
  GOOGLE_GENERATIVE_AI_API_KEY?: string;
  GOOGLE_GENERATIVE_AI_MODEL_NAME?: string;
  JWT_PRIVATE_KEY?: string;
  ML_SERVICE_URL: string;
}

/**
 * Get environment variables for client-side usage
 * Only returns safe-to-expose variables
 */
export function getClientEnv(): ClientEnv {
  const firebaseConfig = process.env.FIREBASE_CONFIG;
  let parsedFirebaseConfig: FirebaseConfig | undefined;

  if (firebaseConfig) {
    try {
      parsedFirebaseConfig = JSON.parse(firebaseConfig);
    } catch {
      console.error('FIREBASE_CONFIG environment variable contains invalid JSON');
    }
  }

  return {
    FIREBASE_CONFIG: parsedFirebaseConfig,
    APP_NAME: process.env.APP_NAME || 'Titanic ML Predictor',
  };
}

/**
 * Get environment variables for server-side usage
 * Includes all environment variables including secrets
 * Falls back to parent project environment variables when local .env values are empty
 */
export function getServerEnv(): ServerEnv {
  return {
    FIREBASE_CONFIG: process.env.FIREBASE_CONFIG,
    FIREBASE_PROJECT_ID: process.env.FIREBASE_PROJECT_ID,
    FIREBASE_SERVICE_ACCOUNT_KEY: process.env.FIREBASE_SERVICE_ACCOUNT_KEY,
    GOOGLE_GENERATIVE_AI_API_KEY: process.env.GOOGLE_GENERATIVE_AI_API_KEY,
    GOOGLE_GENERATIVE_AI_MODEL_NAME: process.env.GOOGLE_GENERATIVE_AI_MODEL_NAME,
    JWT_PRIVATE_KEY: process.env.JWT_PRIVATE_KEY,
    ML_SERVICE_URL: process.env.ML_SERVICE_URL || 'http://localhost:8000',
  };
}