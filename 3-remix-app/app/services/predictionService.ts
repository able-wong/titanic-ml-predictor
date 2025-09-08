/**
 * Shared prediction service for handling ML predictions
 * Used by both API routes and Remix actions
 */

import { mlService, type PredictionRequest } from './mlService';
import { createFirebaseRestApi } from './firebase-restapi';
import { getServerEnv } from '~/utils/env';
import { createAccessToken } from '~/utils/jwt';

export interface PredictionServiceOptions {
  firebaseToken: string;
  predictionData: PredictionRequest;
}

export interface PredictionServiceResult {
  success: boolean;
  prediction?: any;
  input?: PredictionRequest;
  error?: string;
  details?: string;
  missingFields?: string[];
}

/**
 * Verify Firebase ID token and return user ID
 */
async function verifyFirebaseToken(firebaseToken: string): Promise<string> {
  try {
    const serverEnv = getServerEnv();
    const firebaseApi = await createFirebaseRestApi(serverEnv, firebaseToken);
    
    // Token is automatically verified by createFirebaseRestApi
    return firebaseApi.getUid();
  } catch (error) {
    console.error('Firebase token verification failed:', error);
    throw new Error('Invalid authentication token');
  }
}

/**
 * Validate prediction data
 */
function validatePredictionData(predictionData: PredictionRequest): string[] {
  const requiredFields: (keyof PredictionRequest)[] = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked'];
  const missingFields = requiredFields.filter(field => 
    predictionData[field] === null || predictionData[field] === undefined || 
    (typeof predictionData[field] === 'string' && predictionData[field] === '')
  );

  if (missingFields.length > 0) {
    return missingFields;
  }

  // Validate data ranges
  if (predictionData.pclass < 1 || predictionData.pclass > 3) {
    throw new Error('Passenger class must be 1, 2, or 3');
  }

  if (predictionData.age < 0 || predictionData.age > 100) {
    throw new Error('Age must be between 0 and 100');
  }

  if (predictionData.fare < 0) {
    throw new Error('Fare must be non-negative');
  }

  if (!['male', 'female'].includes(predictionData.sex)) {
    throw new Error('Sex must be "male" or "female"');
  }

  if (!['C', 'Q', 'S'].includes(predictionData.embarked)) {
    throw new Error('Embarked must be "C", "Q", or "S"');
  }

  return [];
}

/**
 * Core prediction service function
 */
export async function makePrediction({ firebaseToken, predictionData }: PredictionServiceOptions): Promise<PredictionServiceResult> {
  try {
    // Verify Firebase authentication
    const userId = await verifyFirebaseToken(firebaseToken);

    // Validate prediction data
    const missingFields = validatePredictionData(predictionData);
    if (missingFields.length > 0) {
      return {
        success: false,
        error: 'Missing required fields',
        missingFields
      };
    }

    // Create our own JWT token for ML service authentication
    const mlServiceToken = await createAccessToken({ 
      user_id: userId,
      username: `firebase:${userId}` 
    });

    // Make prediction using ML service
    const prediction = await mlService.predict(predictionData, mlServiceToken);

    return {
      success: true,
      prediction,
      input: predictionData
    };

  } catch (error) {
    console.error('Prediction service error:', error);
    
    // Check if it's an authentication error
    if (error instanceof Error && error.message.includes('Invalid authentication token')) {
      return {
        success: false,
        error: 'Authentication failed',
        details: error.message
      };
    }
    
    return {
      success: false,
      error: 'Failed to make prediction',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}