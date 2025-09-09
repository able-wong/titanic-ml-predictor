import type { MetaFunction, LoaderFunctionArgs } from '@remix-run/node';
import { json } from '@remix-run/node';
import { useLoaderData } from '@remix-run/react';
import React, { useState } from 'react';
import { ProtectedRoute } from '~/components/auth/ProtectedRoute';
import { useAuth } from '~/contexts/AuthContext';
import { getClientEnv } from '~/utils/env';
import type { PredictionServiceResult } from '~/services/predictionService';
import type { PredictionResponse } from '~/services/mlService';

export const meta: MetaFunction = () => {
  return [
    { title: 'ML Prediction - Titanic Predictor' },
    {
      name: 'description',
      content: 'Make survival predictions using machine learning',
    },
  ];
};

export async function loader(_args: LoaderFunctionArgs) {
  const clientEnv = getClientEnv();
  return json({ env: clientEnv });
}


export default function Predict() {
  const { env: _env } = useLoaderData<typeof loader>();
  const { user, loading, initialized, logout, signInWithGoogle } = useAuth();
  const [showResults, setShowResults] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [formRef, setFormRef] = useState<HTMLFormElement | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    localStorage.setItem('theme', newTheme);
    window.location.reload();
  };

  const handleSignOut = async () => {
    try {
      await logout();
      window.location.href = '/';
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  // State to hold Firebase token and prediction result
  const [firebaseToken, setFirebaseToken] = useState<string>('');
  const [predictionResult, setPredictionResult] = useState<PredictionServiceResult | null>(null);

  // Get Firebase ID token when user is available
  React.useEffect(() => {
    if (user) {
      user.getIdToken()
        .then(token => setFirebaseToken(token))
        .catch(error => console.error('Failed to get Firebase ID token:', error));
    }
  }, [user]);

  // Handle form submission with fetch API and Authorization header
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setShowProgress(true);
    setShowResults(false);

    try {
      const formData = new FormData(event.currentTarget);
      
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: formData,
      });

      const result = await response.json();
      setPredictionResult(result as PredictionServiceResult);
    } catch (error) {
      console.error('Prediction request failed:', error);
      setPredictionResult({
        success: false,
        error: 'Failed to make prediction request'
      });
    } finally {
      setIsSubmitting(false);
      setShowProgress(false);
      setShowResults(true);
    }
  };

  // Handle making another prediction
  const handleMakeAnother = () => {
    setShowResults(false);
    setShowProgress(false);
    if (formRef) {
      formRef.reset();
    }
  };


  return (
    <ProtectedRoute requireAuth={true}>
      <div className="min-h-screen bg-base-100">
        {/* Navigation */}
        <div className="navbar bg-base-200">
          <div className="flex-1">
            <a href="/" className="btn btn-ghost text-xl">
              ← Titanic ML Predictor
            </a>
          </div>
          <div className="flex-none">
            <div className="flex items-center gap-4">
              {/* User Auth Section */}
              {initialized && !loading && (
                <div>
                  {user ? (
                    <span className="text-sm">
                      Hi, {user.displayName?.split(' ')[0] || 'User'} |{' '}
                      <button 
                        onClick={() => void handleSignOut()}
                        className="link link-hover"
                      >
                        Sign out
                      </button>
                    </span>
                  ) : (
                    <button 
                      onClick={() => void signInWithGoogle().catch(console.error)}
                      className="link link-hover text-sm"
                    >
                      Sign in
                    </button>
                  )}
                </div>
              )}
              
              {/* Theme Dropdown */}
              <div className="dropdown dropdown-end">
                <button className="link link-hover text-sm">
                  Theme ▼
                </button>
                <ul className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-32">
                  <li>
                    <button onClick={() => handleThemeChange('light')} className="text-sm">
                      Light
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleThemeChange('dark')} className="text-sm">
                      Dark
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleThemeChange('system')} className="text-sm">
                      System
                    </button>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto p-4 max-w-4xl">
          <div className="hero bg-base-200 rounded-lg mb-8">
            <div className="hero-content text-center">
              <div className="max-w-md">
                <h1 className="text-4xl font-bold mb-4">
                  🎯 ML Prediction Form
                </h1>
                <p>
                  Enter passenger details to predict survival probability using our trained machine learning model.
                </p>
              </div>
            </div>
          </div>

          {/* Prediction Form */}
          {!showResults && !showProgress && (
          <form 
            onSubmit={(e) => void handleSubmit(e)}
            ref={(ref) => setFormRef(ref)}
          >
            
            <div className="card bg-base-200 shadow-xl">
              <div className="card-body">
                <h2 className="card-title text-2xl mb-6">Passenger Information</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="form-control w-full">
                    <label className="label" htmlFor="pclass">
                      <span className="label-text font-medium">Passenger Class</span>
                    </label>
                    <select id="pclass" name="pclass" className="select select-bordered w-full" defaultValue="" required>
                      <option disabled value="">Select class</option>
                      <option value="1">1st Class</option>
                      <option value="2">2nd Class</option>
                      <option value="3">3rd Class</option>
                    </select>
                  </div>

                  <div className="form-control w-full">
                    <label className="label" htmlFor="sex">
                      <span className="label-text font-medium">Gender</span>
                    </label>
                    <select id="sex" name="sex" className="select select-bordered w-full" defaultValue="" required>
                      <option disabled value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>

                  <div className="form-control w-full">
                    <label className="label" htmlFor="age">
                      <span className="label-text font-medium">Age</span>
                    </label>
                    <input 
                      id="age"
                      name="age"
                      type="number" 
                      placeholder="Enter age" 
                      className="input input-bordered w-full" 
                      min="0" 
                      max="100"
                      step="0.1"
                      required
                    />
                  </div>

                  <div className="form-control w-full">
                    <label className="label" htmlFor="fare">
                      <span className="label-text font-medium">Fare Paid ($)</span>
                    </label>
                    <input 
                      id="fare"
                      name="fare"
                      type="number" 
                      placeholder="Enter fare amount" 
                      className="input input-bordered w-full" 
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>

                  <div className="form-control w-full">
                    <label className="label" htmlFor="sibsp">
                      <span className="label-text font-medium">Siblings/Spouses</span>
                    </label>
                    <input 
                      id="sibsp"
                      name="sibsp"
                      type="number" 
                      placeholder="Number of siblings/spouses aboard" 
                      className="input input-bordered w-full" 
                      min="0"
                      defaultValue="0"
                      required
                    />
                  </div>

                  <div className="form-control w-full">
                    <label className="label" htmlFor="parch">
                      <span className="label-text font-medium">Parents/Children</span>
                    </label>
                    <input 
                      id="parch"
                      name="parch"
                      type="number" 
                      placeholder="Number of parents/children aboard" 
                      className="input input-bordered w-full" 
                      min="0"
                      defaultValue="0"
                      required
                    />
                  </div>

                  <div className="form-control w-full md:col-span-2">
                    <label className="label" htmlFor="embarked">
                      <span className="label-text font-medium">Port of Embarkation</span>
                    </label>
                    <select id="embarked" name="embarked" className="select select-bordered w-full" defaultValue="" required>
                      <option disabled value="">Select port</option>
                      <option value="C">Cherbourg (C)</option>
                      <option value="Q">Queenstown (Q)</option>
                      <option value="S">Southampton (S)</option>
                    </select>
                  </div>
                </div>

                <div className="card-actions justify-center mt-8">
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-lg"
                    disabled={isSubmitting || !firebaseToken}
                  >
                    {isSubmitting ? (
                      <>
                        <span className="loading loading-spinner loading-sm"></span>
                        Making Prediction...
                      </>
                    ) : (
                      <>
                        🔮 Predict Survival
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </form>
          )}

          {/* Progress Display */}
          {showProgress && (
            <div className="card bg-base-200 shadow-xl mt-6">
              <div className="card-body">
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="loading loading-spinner loading-lg mb-4"></div>
                  <h2 className="text-xl font-semibold mb-2">🧠 Analyzing Your Data...</h2>
                  <p className="text-base-content/70 text-center">
                    Our machine learning models are processing your passenger information.
                    <br />This may take a few seconds.
                  </p>
                  <div className="flex justify-center mt-6">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {predictionResult && showResults && (
            <div className="card bg-base-200 shadow-xl mt-6">
              <div className="card-body">
                <h2 className="card-title text-2xl mb-4">Prediction Results</h2>
                
                {'error' in predictionResult ? (
                  <div className="alert alert-error">
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span><strong>Error:</strong> {predictionResult.error}</span>
                  </div>
                ) : 'prediction' in predictionResult && predictionResult.prediction ? (
                  <div className="space-y-4">
                    {/* Ensemble Result */}
                    <div className={`alert ${(predictionResult.prediction as PredictionResponse).ensemble_result.prediction === 'survived' ? 'alert-success' : 'alert-warning'}`}>
                      <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h3 className="font-bold">
                          {(predictionResult.prediction as PredictionResponse).ensemble_result.prediction === 'survived' ? '✅ Likely Survived' : '❌ Likely Did Not Survive'}
                        </h3>
                        <div className="text-xs">
                          Survival Probability: {Math.round((predictionResult.prediction as PredictionResponse).ensemble_result.probability * 100)}% 
                          ({(predictionResult.prediction as PredictionResponse).ensemble_result.confidence_level} confidence)
                        </div>
                      </div>
                    </div>

                    {/* Individual Model Results */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="stats shadow">
                        <div className="stat">
                          <div className="stat-title">Logistic Regression</div>
                          <div className="stat-value text-sm">
                            {Math.round((predictionResult.prediction as PredictionResponse).individual_models.logistic_regression.probability * 100)}%
                          </div>
                          <div className="stat-desc">
                            {(predictionResult.prediction as PredictionResponse).individual_models.logistic_regression.prediction === 'survived' ? 'Survived' : 'Did not survive'}
                          </div>
                        </div>
                      </div>

                      <div className="stats shadow">
                        <div className="stat">
                          <div className="stat-title">Decision Tree</div>
                          <div className="stat-value text-sm">
                            {Math.round((predictionResult.prediction as PredictionResponse).individual_models.decision_tree.probability * 100)}%
                          </div>
                          <div className="stat-desc">
                            {(predictionResult.prediction as PredictionResponse).individual_models.decision_tree.prediction === 'survived' ? 'Survived' : 'Did not survive'}
                          </div>
                        </div>
                      </div>
                    </div>

                    <button 
                      onClick={handleMakeAnother}
                      className="btn btn-primary btn-sm"
                    >
                      🔄 Make Another Prediction
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}