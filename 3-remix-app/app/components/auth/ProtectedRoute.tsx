/**
 * Protected Route Component
 * Wraps content that requires authentication
 */

import React, { type ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { SignInButton } from './SignInButton';

export interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
  loadingFallback?: ReactNode;
  requireAuth?: boolean;
}

export function ProtectedRoute({ 
  children, 
  fallback,
  loadingFallback,
  requireAuth = true 
}: ProtectedRouteProps) {
  const { user, loading, initialized } = useAuth();

  // Show loading state while Firebase initializes or auth state is loading
  if (!initialized || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        {loadingFallback || (
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading...</p>
          </div>
        )}
      </div>
    );
  }

  // If authentication is not required, always show children
  if (!requireAuth) {
    return <>{children}</>;
  }

  // If user is authenticated, show protected content
  if (user) {
    return <>{children}</>;
  }

  // Show sign-in prompt for unauthenticated users
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      {fallback || (
        <div className="max-w-md w-full mx-auto p-6">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Sign In Required
            </h1>
            <p className="text-gray-600 mb-6">
              Please sign in to access the Titanic ML Predictor.
            </p>
            <SignInButton className="w-full justify-center mb-4" />
            <a 
              href="/" 
              className="inline-block text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              ← Back to Home
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Auth Guard Hook - for use in route components
 */
export function useAuthGuard() {
  const { user, loading, initialized } = useAuth();
  
  return {
    isAuthenticated: !!user,
    isLoading: !initialized || loading,
    user,
  };
}