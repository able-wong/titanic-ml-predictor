import type { MetaFunction, LoaderFunctionArgs } from '@remix-run/node';
import { json } from '@remix-run/node';
import { useLoaderData, useNavigate } from '@remix-run/react';
import { createLogger } from '~/utils/logger';
import { useAuth } from '~/contexts/AuthContext';
import { SignInButton } from '~/components/auth/SignInButton';
import { UserProfile } from '~/components/auth/UserProfile';

export const meta: MetaFunction = () => {
  return [
    { title: 'Titanic ML Predictor' },
    {
      name: 'description',
      content: 'Predict Titanic passenger survival using machine learning',
    },
  ];
};

export async function loader(_args: LoaderFunctionArgs) {
  const logger = createLogger();

  logger.info('Index page loaded', {
    route: '/_index',
    timestamp: new Date().toISOString(),
    requestId: Math.random().toString(36).substring(7),
  });

  // Pass client environment variables to the browser
  const { getClientEnv } = await import('~/utils/env');
  const clientEnv = getClientEnv();

  return json({ 
    success: true,
    env: clientEnv 
  });
}

export default function Index() {
  const { env } = useLoaderData<typeof loader>();
  const { user, loading, initialized, logout, signInWithGoogle, authChecked } = useAuth();
  const navigate = useNavigate();

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    localStorage.setItem('theme', newTheme);
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-base-100">
      <div className="navbar bg-base-200">
        <div className="flex-1">
          <span className="btn btn-ghost text-xl">
            Titanic ML Predictor
          </span>
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
                      onClick={() => logout().catch(console.error)}
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

      <div className="container mx-auto p-4 space-y-8">
        {/* Welcome Hero Section */}
        <div className="hero bg-base-200 rounded-lg">
          <div className="hero-content text-center">
            <div className="max-w-lg">
              <h1 className="text-4xl md:text-5xl font-bold whitespace-nowrap">
                🚢 Titanic ML Predictor
              </h1>
              <p className="py-6">
                Use machine learning to predict passenger survival on the Titanic. 
                {user 
                  ? ` Welcome back, ${user.displayName || 'user'}! Ready to make predictions?` 
                  : ' Sign in to start making predictions.'
                }
              </p>
              <div className="flex justify-center">
                {/* Show sign-in button by default, switch to "Start Predicting" when authenticated */}
                {user ? (
                  <button 
                    onClick={() => navigate('/predict')}
                    className="btn btn-primary btn-lg"
                  >
                    Start Predicting
                  </button>
                ) : (
                  <SignInButton 
                    className="btn btn-primary btn-lg justify-center" 
                    onSuccess={() => {
                      // Navigate to prediction form after successful login
                      navigate('/predict');
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Learning & Tech Stack Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="card bg-base-200 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">🧠 Machine Learning</h2>
              <p>Scikit-learn pipeline with Logistic Regression and Decision Tree models. Features engineering includes age groups, fare categories, and family size from passenger data.</p>
              <div className="text-xs mt-2 space-y-1">
                <div><strong>Training:</strong> 80/20 train-test split on public Titanic dataset</div>
                <div><strong>Models:</strong> Logistic Regression & Decision Tree with ensemble averaging</div>
                <div><strong>Features:</strong> Age, class, gender, fare, family size, embarkation port</div>
              </div>
              <div className="stats stats-vertical text-xs mt-2">
                <div className="stat">
                  <div className="stat-title">Model Accuracy</div>
                  <div className="stat-value text-sm">~82%</div>
                </div>
              </div>
            </div>
          </div>

          <div className="card bg-base-200 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">🏗️ Full Stack</h2>
              <p>Remix.js frontend with server-side rendering connecting to production FastAPI ML service with JWT authentication and rate limiting.</p>
              <div className="text-xs mt-2 space-y-1">
                <div><strong>Frontend:</strong> Remix SSR, TypeScript, Firebase Auth, DaisyUI</div>
                <div><strong>Backend:</strong> FastAPI with lazy loading, JWT RS256, Redis rate limiting</div>
                <div><strong>API Features:</strong> Request tracing, health monitoring, input validation</div>
              </div>
              <div className="text-xs mt-2">
                <span className="badge badge-sm">Remix</span>{' '}
                <span className="badge badge-sm">FastAPI</span>{' '}
                <span className="badge badge-sm">Firebase</span>{' '}
                <span className="badge badge-sm">JWT</span>
              </div>
            </div>
          </div>

          <div className="card bg-base-200 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">🚀 DevOps & CI/CD</h2>
              <p>Multi-environment deployment pipeline with automated testing, security scanning, and containerized deployments to Google Cloud Run and Firebase App Hosting.</p>
              <div className="text-xs mt-2 space-y-1">
                <div><strong>Frontend:</strong> Firebase App Hosting with automatic builds from git</div>
                <div><strong>Backend:</strong> Google Cloud Run with Docker containers and health checks</div>
                <div><strong>Pipeline:</strong> GitHub Actions, Ruff linting, pytest testing, security scans</div>
              </div>
              <div className="text-xs mt-2">
                <span className="badge badge-sm">Firebase</span>{' '}
                <span className="badge badge-sm">Cloud Run</span>{' '}
                <span className="badge badge-sm">Docker</span>{' '}
                <span className="badge badge-sm">Actions</span>
              </div>
            </div>
          </div>
        </div>


      </div>
    </div>
  );
}
