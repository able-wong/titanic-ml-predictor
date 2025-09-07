/**
 * API route for ML predictions
 * Handles form submissions and communicates with the FastAPI ML service
 */

import type { ActionFunctionArgs } from '@remix-run/node';
import { json } from '@remix-run/node';
import { mlService, type PredictionRequest } from '~/services/mlService';
import { createFirebaseRestApi } from '~/services/firebase-restapi';
import { getServerEnv } from '~/utils/env';
import { createAccessToken } from '~/utils/jwt';

/**
 * Verify Firebase ID token using the existing Firebase REST API service
 */
async function verifyAuthToken(request: Request): Promise<string | null> {
  const authHeader = request.headers.get('Authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }

  const token = authHeader.substring(7);
  
  try {
    const serverEnv = getServerEnv();
    const firebaseApi = await createFirebaseRestApi(serverEnv, token);
    
    // Token is automatically verified by createFirebaseRestApi
    // Get the validated user ID
    const userId = firebaseApi.getUid();
    return userId;
  } catch (error) {
    console.error('Firebase token verification failed:', error);
    return null;
  }
}

export async function action({ request }: ActionFunctionArgs) {
  if (request.method !== 'POST') {
    return json({ error: 'Method not allowed' }, { status: 405 });
  }

  try {
    // Verify authentication first
    const userId = await verifyAuthToken(request);
    
    if (!userId) {
      return json({ error: 'Authentication required' }, { status: 401 });
    }

    // Parse the form data
    const formData = await request.formData();
    
    // Extract prediction parameters
    const predictionData: PredictionRequest = {
      pclass: parseInt(formData.get('pclass') as string),
      sex: formData.get('sex') as string,
      age: parseFloat(formData.get('age') as string),
      sibsp: parseInt(formData.get('sibsp') as string),
      parch: parseInt(formData.get('parch') as string),
      fare: parseFloat(formData.get('fare') as string),
      embarked: formData.get('embarked') as string,
    };

    // Validate required fields
    const requiredFields: (keyof PredictionRequest)[] = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked'];
    const missingFields = requiredFields.filter(field => 
      predictionData[field] === null || predictionData[field] === undefined || 
      (typeof predictionData[field] === 'string' && predictionData[field] === '')
    );

    if (missingFields.length > 0) {
      return json({ 
        error: 'Missing required fields', 
        missingFields 
      }, { status: 400 });
    }

    // Validate data ranges
    if (predictionData.pclass < 1 || predictionData.pclass > 3) {
      return json({ error: 'Passenger class must be 1, 2, or 3' }, { status: 400 });
    }

    if (predictionData.age < 0 || predictionData.age > 100) {
      return json({ error: 'Age must be between 0 and 100' }, { status: 400 });
    }

    if (predictionData.fare < 0) {
      return json({ error: 'Fare must be non-negative' }, { status: 400 });
    }

    if (!['male', 'female'].includes(predictionData.sex)) {
      return json({ error: 'Sex must be "male" or "female"' }, { status: 400 });
    }

    if (!['C', 'Q', 'S'].includes(predictionData.embarked)) {
      return json({ error: 'Embarked must be "C", "Q", or "S"' }, { status: 400 });
    }

    // Create our own JWT token for ML service authentication
    const mlServiceToken = await createAccessToken({ 
      user_id: userId,
      username: `firebase:${userId}` 
    });

    // Make prediction using ML service with our JWT token
    const prediction = await mlService.predict(predictionData, mlServiceToken);

    return json({
      success: true,
      prediction,
      input: predictionData
    });

  } catch (error) {
    console.error('Prediction API error:', error);
    
    // Check if it's an authentication error
    if (error instanceof Error && error.message.includes('401')) {
      return json({
        error: 'Authentication failed',
        details: error.message
      }, { status: 401 });
    }
    
    return json({
      error: 'Failed to make prediction',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}