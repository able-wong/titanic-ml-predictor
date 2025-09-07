import type { MetaFunction, LoaderFunctionArgs } from '@remix-run/node';
import { json } from '@remix-run/node';
import { useLoaderData } from '@remix-run/react';
import { ProtectedRoute } from '~/components/auth/ProtectedRoute';
import { useAuth } from '~/contexts/AuthContext';
import { getClientEnv } from '~/utils/env';

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
  const { env } = useLoaderData<typeof loader>();
  const { user, loading, initialized, logout, signInWithGoogle } = useAuth();

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
                        onClick={handleSignOut}
                        className="link link-hover"
                      >
                        Sign out
                      </button>
                    </span>
                  ) : (
                    <button 
                      onClick={() => signInWithGoogle().catch(console.error)}
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

          {/* Prediction Form Placeholder */}
          <div className="card bg-base-200 shadow-xl">
            <div className="card-body">
              <h2 className="card-title text-2xl mb-6">Passenger Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Passenger Class</span>
                  </label>
                  <select className="select select-bordered w-full" defaultValue="">
                    <option disabled value="">Select class</option>
                    <option value="1">1st Class</option>
                    <option value="2">2nd Class</option>
                    <option value="3">3rd Class</option>
                  </select>
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Gender</span>
                  </label>
                  <select className="select select-bordered w-full" defaultValue="">
                    <option disabled value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Age</span>
                  </label>
                  <input 
                    type="number" 
                    placeholder="Enter age" 
                    className="input input-bordered w-full" 
                    min="0" 
                    max="100"
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Fare Paid ($)</span>
                  </label>
                  <input 
                    type="number" 
                    placeholder="Enter fare amount" 
                    className="input input-bordered w-full" 
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Siblings/Spouses</span>
                  </label>
                  <input 
                    type="number" 
                    placeholder="Number of siblings/spouses aboard" 
                    className="input input-bordered w-full" 
                    min="0"
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Parents/Children</span>
                  </label>
                  <input 
                    type="number" 
                    placeholder="Number of parents/children aboard" 
                    className="input input-bordered w-full" 
                    min="0"
                  />
                </div>

                <div className="form-control w-full md:col-span-2">
                  <label className="label">
                    <span className="label-text font-medium">Port of Embarkation</span>
                  </label>
                  <select className="select select-bordered w-full" defaultValue="">
                    <option disabled value="">Select port</option>
                    <option value="C">Cherbourg (C)</option>
                    <option value="Q">Queenstown (Q)</option>
                    <option value="S">Southampton (S)</option>
                  </select>
                </div>
              </div>

              <div className="card-actions justify-center mt-8">
                <button className="btn btn-primary btn-lg">
                  🔮 Predict Survival
                </button>
              </div>

              {/* Placeholder for results */}
              <div className="alert alert-info mt-6">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>
                  <strong>Coming Soon:</strong> This form will connect to the ML service API to provide real-time survival probability predictions.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}