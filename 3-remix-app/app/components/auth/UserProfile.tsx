/**
 * User Profile Component
 * Shows user information and provides sign-out functionality
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export interface UserProfileProps {
  className?: string;
  showEmail?: boolean;
  showSignOut?: boolean;
  onSignOut?: () => void;
}

export function UserProfile({ 
  className = '',
  showEmail = true,
  showSignOut = true,
  onSignOut 
}: UserProfileProps) {
  const { user, logout } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  if (!user) {
    return null;
  }

  const handleSignOut = async () => {
    if (isSigningOut) return;
    
    setIsSigningOut(true);
    
    try {
      await logout();
      onSignOut?.();
    } catch (error: any) {
      console.error('Sign-out error:', error);
    } finally {
      setIsSigningOut(false);
    }
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* User Avatar */}
      {user.photoURL ? (
        <img
          src={user.photoURL}
          alt={user.displayName || 'User'}
          className="w-8 h-8 rounded-full border border-gray-300"
        />
      ) : (
        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
          <span className="text-gray-600 text-sm font-medium">
            {user.displayName?.charAt(0)?.toUpperCase() || 'U'}
          </span>
        </div>
      )}

      {/* User Info */}
      <div className="flex-1 min-w-0">
        {user.displayName && (
          <div className="text-sm font-medium text-gray-900 truncate">
            {user.displayName}
          </div>
        )}
        {showEmail && user.email && (
          <div className="text-xs text-gray-500 truncate">
            {user.email}
          </div>
        )}
      </div>

      {/* Sign Out Button */}
      {showSignOut && (
        <button
          type="button"
          onClick={handleSignOut}
          disabled={isSigningOut}
          className="
            px-3 py-1 text-xs font-medium text-gray-600
            hover:text-gray-900 hover:bg-gray-100
            focus:outline-none focus:ring-1 focus:ring-gray-300
            disabled:opacity-50 disabled:cursor-not-allowed
            rounded transition-colors duration-200
          "
        >
          {isSigningOut ? 'Signing out...' : 'Sign out'}
        </button>
      )}
    </div>
  );
}

/**
 * Compact User Profile for headers/navbars
 */
export function CompactUserProfile({ className = '' }: { className?: string }) {
  return (
    <UserProfile 
      className={`${className} max-w-xs`}
      showEmail={false}
      showSignOut={true}
    />
  );
}