/**
 * Firebase initialization and configuration
 * Handles client-side Firebase setup for authentication
 */

import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getAuth, type Auth } from 'firebase/auth';
import type { ClientEnv } from './env';

let firebaseApp: FirebaseApp | null = null;
let firebaseAuth: Auth | null = null;

/**
 * Initialize Firebase app with client configuration
 */
export function getFirebaseApp(env: ClientEnv): FirebaseApp {
  if (firebaseApp) {
    console.log('DEBUG: Returning existing Firebase app');
    return firebaseApp;
  }
  
  console.log('DEBUG: Initializing new Firebase app');
  console.log('DEBUG: env.FIREBASE_CONFIG exists:', !!env.FIREBASE_CONFIG);
  console.log('DEBUG: env.FIREBASE_CONFIG has apiKey:', !!env.FIREBASE_CONFIG?.apiKey);
  console.log('DEBUG: env.FIREBASE_CONFIG has projectId:', !!env.FIREBASE_CONFIG?.projectId);
  
  if (!env.FIREBASE_CONFIG) {
    console.error('DEBUG: Firebase configuration is missing from env object');
    throw new Error(
      'Firebase configuration not found. Please set FIREBASE_CONFIG environment variable.'
    );
  }

  try {
    console.log('DEBUG: Attempting to initialize Firebase app with config:', {
      apiKey: env.FIREBASE_CONFIG.apiKey ? 'present' : 'missing',
      projectId: env.FIREBASE_CONFIG.projectId,
      authDomain: env.FIREBASE_CONFIG.authDomain
    });
    
    firebaseApp = initializeApp(env.FIREBASE_CONFIG);
    console.log('DEBUG: Firebase app initialized successfully');
    return firebaseApp;
  } catch (error) {
    console.error('DEBUG: Failed to initialize Firebase app:', error);
    console.error('DEBUG: Firebase config that caused error:', env.FIREBASE_CONFIG);
    throw new Error('Firebase initialization failed. Please check your configuration.');
  }
}

/**
 * Get Firebase Auth instance
 */
export async function getFirebaseAuth(env: ClientEnv): Promise<Auth> {
  if (firebaseAuth) {
    return firebaseAuth;
  }

  try {
    const app = getFirebaseApp(env);
    firebaseAuth = getAuth(app);
    return firebaseAuth;
  } catch (error) {
    console.error('Failed to initialize Firebase Auth:', error);
    throw new Error('Firebase Auth initialization failed.');
  }
}

/**
 * Check if Firebase is properly configured
 */
export function isFirebaseConfigured(env: ClientEnv): boolean {
  try {
    return !!(env.FIREBASE_CONFIG && env.FIREBASE_CONFIG.apiKey);
  } catch {
    return false;
  }
}