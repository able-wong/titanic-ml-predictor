/**
 * JWT utilities for handling authentication tokens
 * Provides functionality to create, verify and decode JWT tokens
 */

import { SignJWT, jwtVerify, type JWTPayload } from 'jose';
import { getServerEnv } from './env';

export interface JWTTokenData extends Record<string, unknown> {
  user_id: string;
  username?: string;
}

export interface DecodedToken extends JWTPayload, JWTTokenData {}

/**
 * Create a signed JWT token for the given user data
 */
export async function createAccessToken(
  data: JWTTokenData,
  expiresIn?: string
): Promise<string> {
  const env = getServerEnv();
  
  if (!env.JWT_PRIVATE_KEY) {
    throw new Error('JWT_PRIVATE_KEY environment variable is required');
  }

  // Use provided expiresIn or fall back to environment variable (default: 5m)
  const ttl = expiresIn || env.JWT_TTL;

  // Convert PEM private key to KeyLike object
  const privateKey = await importPrivateKey(env.JWT_PRIVATE_KEY);
  
  const now = Math.floor(Date.now() / 1000);
  const expiration = getExpirationTime(ttl);

  const jwt = await new SignJWT(data)
    .setProtectedHeader({ alg: 'RS256' })
    .setIssuedAt(now)
    .setExpirationTime(now + expiration)
    .setIssuer('titanic-ml-predictor')
    .setAudience('ml-service')
    .sign(privateKey);

  return jwt;
}

/**
 * Verify and decode a JWT token
 */
export async function verifyAccessToken(token: string): Promise<DecodedToken> {
  const env = getServerEnv();
  
  if (!env.JWT_PRIVATE_KEY) {
    throw new Error('JWT_PRIVATE_KEY environment variable is required');
  }

  // For verification, we derive the public key from the private key
  const publicKey = await importPublicKeyFromPrivate(env.JWT_PRIVATE_KEY);
  
  try {
    const { payload } = await jwtVerify(token, publicKey, {
      issuer: 'titanic-ml-predictor',
      audience: 'ml-service',
    });

    return payload as DecodedToken;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`JWT verification failed: ${errorMessage}`);
  }
}

/**
 * Decode JWT token without verification (use carefully)
 */
export function decodeToken(token: string): JWTPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }
    
    const payload = parts[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded;
  } catch {
    return null;
  }
}

/**
 * Check if a token is expired
 */
export function isTokenExpired(token: string): boolean {
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) {
    return true;
  }
  
  const now = Math.floor(Date.now() / 1000);
  return decoded.exp < now;
}

/**
 * Import private key from PEM string
 */
async function importPrivateKey(privateKeyPem: string): Promise<CryptoKey> {
  // Clean up the PEM string
  const cleaned = privateKeyPem
    .replace(/-----BEGIN PRIVATE KEY-----/g, '')
    .replace(/-----END PRIVATE KEY-----/g, '')
    .replace(/-----BEGIN RSA PRIVATE KEY-----/g, '')
    .replace(/-----END RSA PRIVATE KEY-----/g, '')
    .replace(/\s/g, '');
    
  try {
    const binaryData = Uint8Array.from(atob(cleaned), char => char.charCodeAt(0));
    
    return await crypto.subtle.importKey(
      'pkcs8',
      binaryData,
      {
        name: 'RSASSA-PKCS1-v1_5',
        hash: 'SHA-256',
      },
      false,
      ['sign']
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to import private key: ${errorMessage}`);
  }
}

/**
 * Import public key from PEM string (for verification)
 */
async function importPublicKeyFromPrivate(privateKeyPem: string): Promise<CryptoKey> {
  // In production, you should have a separate public key
  // This is a simplified approach for development
  try {
    const cleaned = privateKeyPem
      .replace(/-----BEGIN PRIVATE KEY-----/g, '')
      .replace(/-----END PRIVATE KEY-----/g, '')
      .replace(/-----BEGIN RSA PRIVATE KEY-----/g, '')
      .replace(/-----END RSA PRIVATE KEY-----/g, '')
      .replace(/\s/g, '');
      
    const binaryData = Uint8Array.from(atob(cleaned), char => char.charCodeAt(0));
    
    // Import as private key first
    const privateKey = await crypto.subtle.importKey(
      'pkcs8',
      binaryData,
      {
        name: 'RSASSA-PKCS1-v1_5',
        hash: 'SHA-256',
      },
      true,
      ['sign']
    );
    
    // Export the public key portion
    const publicKeyData = await crypto.subtle.exportKey('spki', privateKey);
    
    return await crypto.subtle.importKey(
      'spki',
      publicKeyData,
      {
        name: 'RSASSA-PKCS1-v1_5',
        hash: 'SHA-256',
      },
      false,
      ['verify']
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to derive public key: ${errorMessage}`);
  }
}

/**
 * Convert expiration string to seconds
 */
function getExpirationTime(expiresIn: string): number {
  const match = expiresIn.match(/^(\d+)([smhd])$/);
  if (!match) {
    throw new Error('Invalid expiration format. Use format like "1h", "30m", "3600s"');
  }
  
  const [, value, unit] = match;
  const numValue = parseInt(value, 10);
  
  switch (unit) {
    case 's': return numValue;
    case 'm': return numValue * 60;
    case 'h': return numValue * 60 * 60;
    case 'd': return numValue * 60 * 60 * 24;
    default: throw new Error('Invalid time unit');
  }
}