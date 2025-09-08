/**
 * API route for ML predictions
 * Handles form submissions and communicates with the FastAPI ML service
 */

import type { ActionFunctionArgs } from '@remix-run/node';
import { json } from '@remix-run/node';
import { makePrediction } from '~/services/predictionService';
import type { PredictionRequest } from '~/services/mlService';

export async function action({ request }: ActionFunctionArgs) {
  if (request.method !== 'POST') {
    return json({ error: 'Method not allowed' }, { status: 405 });
  }

  // Get Firebase token from Authorization header
  const authHeader = request.headers.get('Authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return json({ error: 'Authentication required' }, { status: 401 });
  }

  const firebaseToken = authHeader.substring(7);

  // Parse form data
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

  // Use shared prediction service
  const result = await makePrediction({ firebaseToken, predictionData });

  if (!result.success) {
    const status = result.error === 'Authentication failed' ? 401 : 
                   result.missingFields ? 400 : 500;
    return json(result, { status });
  }

  return json(result);
}