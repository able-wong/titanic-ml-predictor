#!/usr/bin/env node

/**
 * Test script to verify JWT flow between Remix and ML service
 */

import { createAccessToken } from './app/utils/jwt.js';

async function testJWTFlow() {
  console.log('🔧 Testing JWT Flow between Remix and ML Service\n');
  
  try {
    // 1. Generate a JWT token using Remix utilities
    console.log('1. Generating JWT token using Remix utilities...');
    const token = await createAccessToken({
      user_id: 'test-firebase-user-123',
      username: 'firebase:test-user'
    });
    
    console.log('✅ Token generated successfully');
    console.log(`   Token (first 50 chars): ${token.substring(0, 50)}...`);
    
    // 2. Test the token with ML service health endpoint (doesn't require auth)
    console.log('\n2. Testing ML service connectivity...');
    const healthResponse = await fetch('http://localhost:8000/health');
    const healthData = await healthResponse.json();
    console.log('✅ ML service is running:', healthData.status);
    
    // 3. Test the token with ML service prediction endpoint
    console.log('\n3. Testing prediction with JWT token...');
    const predictionData = {
      pclass: 1,
      sex: 'female',
      age: 30,
      sibsp: 1,
      parch: 0,
      fare: 100.0,
      embarked: 'S'
    };
    
    const predictResponse = await fetch('http://localhost:8000/predict', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(predictionData)
    });
    
    if (predictResponse.ok) {
      const prediction = await predictResponse.json();
      console.log('✅ Prediction successful!');
      console.log('   Ensemble result:', prediction.ensemble_result.prediction);
      console.log('   Survival probability:', Math.round(prediction.ensemble_result.probability * 100) + '%');
      console.log('   Confidence:', prediction.ensemble_result.confidence_level);
    } else {
      const errorText = await predictResponse.text();
      console.log('❌ Prediction failed:', predictResponse.status);
      console.log('   Error:', errorText);
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testJWTFlow();