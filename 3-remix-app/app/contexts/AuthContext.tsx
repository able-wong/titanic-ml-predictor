/**
 * Firebase Authentication Context
 * Provides Firebase Auth state management and user session handling
 */

import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { 
  User, 
  GoogleAuthProvider, 
  signInWithPopup, 
  signOut, 
  onAuthStateChanged,
  type Auth 
} from 'firebase/auth';
import { getFirebaseAuth } from '../utils/firebase';
import type { ClientEnv } from '../utils/env';

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  initialized: boolean;
  authChecked: boolean; // True once auth state has been determined
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {
  children: ReactNode;
  env: ClientEnv;
}

export function AuthProvider({ children, env }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false); // For auth operations
  const [initialized, setInitialized] = useState(false);
  const [authChecked, setAuthChecked] = useState(false); // Track if auth state has been checked

  useEffect(() => {
    let auth: Auth;
    let unsubscribe: (() => void) | undefined;

    const initializeAuth = async () => {
      try {
        auth = await getFirebaseAuth(env);
        setInitialized(true);
        
        // Set up auth state listener - this will fire when Firebase determines auth state
        unsubscribe = onAuthStateChanged(auth, (user) => {
          setUser(user);
          setAuthChecked(true); // Mark as checked when we get the first callback
          setLoading(false); // Reset loading after auth operations
        });
      } catch (error) {
        console.error('Failed to initialize Firebase Auth:', error);
        setLoading(false);
        setInitialized(true);
        setAuthChecked(true);
      }
    };

    initializeAuth();

    // Cleanup function
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [env]);

  const signInWithGoogle = async () => {
    if (!initialized) {
      throw new Error('Firebase Auth not initialized');
    }

    setLoading(true); // Set loading when sign-in starts

    try {
      const auth = await getFirebaseAuth(env);
      const provider = new GoogleAuthProvider();
      
      // Request additional scopes if needed
      provider.addScope('email');
      provider.addScope('profile');
      
      const result = await signInWithPopup(auth, provider);
      
      // The user is automatically set via onAuthStateChanged listener
      console.log('Successfully signed in:', result.user.displayName);
    } catch (error: any) {
      console.error('Google sign-in error:', error);
      
      // Handle specific Firebase Auth errors
      if (error.code === 'auth/popup-closed-by-user') {
        throw new Error('Sign-in was cancelled. Please try again.');
      } else if (error.code === 'auth/popup-blocked') {
        throw new Error('Pop-up blocked. Please allow pop-ups and try again.');
      } else {
        throw new Error(`Sign-in failed: ${error.message}`);
      }
    } finally {
      setLoading(false); // Always reset loading state
    }
  };

  const logout = async () => {
    if (!initialized) {
      throw new Error('Firebase Auth not initialized');
    }

    setLoading(true); // Set loading when sign-out starts

    try {
      const auth = await getFirebaseAuth(env);
      await signOut(auth);
      console.log('Successfully signed out');
    } catch (error: any) {
      console.error('Sign-out error:', error);
      throw new Error(`Sign-out failed: ${error.message}`);
    } finally {
      setLoading(false); // Always reset loading state
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    signInWithGoogle,
    logout,
    initialized,
    authChecked,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

