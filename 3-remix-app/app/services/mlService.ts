/**
 * ML Service API Client
 * Handles communication with the FastAPI ML service
 */

import { getServerEnv } from '~/utils/env';
import { createAccessToken } from '~/utils/jwt';

export interface PredictionRequest {
  pclass: number;
  sex: string;
  age: number;
  sibsp: number;
  parch: number;
  fare: number;
  embarked: string;
}

export interface ModelPrediction {
  probability: number;
  prediction: 'survived' | 'died';
}

export interface PredictionResponse {
  individual_models: {
    logistic_regression: ModelPrediction;
    decision_tree: ModelPrediction;
  };
  ensemble_result: {
    probability: number;
    prediction: 'survived' | 'died';
    confidence: number;
    confidence_level: 'low' | 'medium' | 'high';
  };
}

export interface MLServiceHealth {
  status: string;
  models_loaded: boolean;
  preprocessor_ready: boolean;
  model_accuracy: {
    logistic_regression: number;
    decision_tree: number;
    ensemble: number;
  };
}

class MLService {
  private baseUrl: string;

  constructor() {
    // Get ML service URL from environment
    const env = getServerEnv();
    this.baseUrl = env.ML_SERVICE_URL || 'http://localhost:8000';
  }

  /**
   * Generate JWT token for API authentication
   */
  private async generateJwtToken(userId: string): Promise<string> {
    return await createAccessToken({ user_id: userId });
  }

  /**
   * Make authenticated API request
   */
  private async makeRequest<T>(
    endpoint: string,
    userId: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers || {}) as Record<string, string>),
    };

    // Generate JWT token for authentication
    const jwtToken = await this.generateJwtToken(userId);
    headers.Authorization = `Bearer ${jwtToken}`;

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `ML Service error (${response.status}): ${errorText}`
      );
    }

    return response.json();
  }

  /**
   * Make unauthenticated API request (for health checks)
   */
  private async makePublicRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers || {}) as Record<string, string>),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `ML Service error (${response.status}): ${errorText}`
      );
    }

    return response.json();
  }

  /**
   * Check ML service health
   */
  async checkHealth(): Promise<MLServiceHealth> {
    return this.makePublicRequest<MLServiceHealth>('/health');
  }

  /**
   * Make survival prediction
   */
  async predict(data: PredictionRequest, jwtToken: string): Promise<PredictionResponse> {
    const url = `${this.baseUrl}/predict`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${jwtToken}`,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `ML Service error (${response.status}): ${errorText}`
      );
    }

    return response.json();
  }

  /**
   * Get model information
   */
  async getModelInfo(userId: string): Promise<unknown> {
    return this.makeRequest('/model-info', userId);
  }
}

// Export singleton instance
export const mlService = new MLService();