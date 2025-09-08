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
  JWT_TTL: string;
  ML_SERVICE_URL: string;
}

/**
 * Convert hex string back to original string
 */
function hexToString(hex: string): string {
  return Buffer.from(hex, 'hex').toString();
}

/**
 * Get environment variables for client-side usage
 * Only returns safe-to-expose variables
 */
export function getClientEnv(): ClientEnv {
  const firebaseConfig = process.env.FIREBASE_CONFIG;
  const firebaseApiKeyHex = process.env.FIREBASE_API_KEY_HEX;
  let parsedFirebaseConfig: FirebaseConfig | undefined;

  // Debug logging for Firebase configuration
  console.log('DEBUG: process.env.FIREBASE_CONFIG exists:', !!firebaseConfig);
  console.log('DEBUG: process.env.FIREBASE_CONFIG length:', firebaseConfig?.length || 0);
  console.log('DEBUG: process.env.FIREBASE_CONFIG starts with {:', firebaseConfig?.startsWith('{'));
  console.log('DEBUG: process.env.FIREBASE_API_KEY_HEX exists:', !!firebaseApiKeyHex);
  console.log('DEBUG: process.env.DUMMY_SECRET_TEST exists:', !!process.env.DUMMY_SECRET_TEST);
  console.log('DEBUG: process.env.JWT_PRIVATE_KEY exists:', !!process.env.JWT_PRIVATE_KEY);

  if (firebaseConfig) {
    try {
      parsedFirebaseConfig = JSON.parse(firebaseConfig);
      console.log('DEBUG: Parsed Firebase config successfully');
      console.log('DEBUG: Firebase config has apiKey:', !!parsedFirebaseConfig?.apiKey);
      console.log('DEBUG: Firebase config has projectId:', !!parsedFirebaseConfig?.projectId);
      
      // If apiKey is missing from main config, convert hex to string and use it
      if (!parsedFirebaseConfig?.apiKey && firebaseApiKeyHex) {
        console.log('DEBUG: Converting hex API key and filling missing apiKey');
        try {
          const apiKey = hexToString(firebaseApiKeyHex);
          parsedFirebaseConfig.apiKey = apiKey;
          console.log('DEBUG: Successfully converted hex to API key');
        } catch (error) {
          console.error('DEBUG: Failed to convert hex API key:', error);
        }
      }
    } catch (error) {
      console.error('FIREBASE_CONFIG environment variable contains invalid JSON:', error);
      console.error('DEBUG: Raw FIREBASE_CONFIG value:', firebaseConfig);
    }
  } else {
    console.error('DEBUG: FIREBASE_CONFIG environment variable is not set');
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
    JWT_TTL: process.env.JWT_TTL || '5m',
    ML_SERVICE_URL: process.env.ML_SERVICE_URL || 'http://localhost:8000',
  };
}