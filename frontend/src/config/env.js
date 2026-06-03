/**
 * Environment Configuration
 * 
 * Centralized environment variable management for the frontend application.
 * All environment variables should be imported from this file.
 */

export const ENV = {
  // API Configuration
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  // Firebase Configuration
  FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY || '',
  FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  FIREBASE_STORAGE_BUCKET: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  FIREBASE_MESSAGING_SENDER_ID: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  FIREBASE_APP_ID: import.meta.env.VITE_FIREBASE_APP_ID || '',
  FIREBASE_MEASUREMENT_ID: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || '',

  // Local development auth fallback
  DEV_AUTH_EMAIL: import.meta.env.VITE_DEV_AUTH_EMAIL || '',
  DEV_AUTH_PASSWORD: import.meta.env.VITE_DEV_AUTH_PASSWORD || '',
  DEV_AUTH_TOKEN: import.meta.env.VITE_DEV_AUTH_TOKEN || '',
  DEV_AUTH_DISPLAY_NAME: import.meta.env.VITE_DEV_AUTH_DISPLAY_NAME || 'Local Test User',
  
  // Application Metadata
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '0.1.0',
}

// Readonly to prevent accidental mutations
Object.freeze(ENV)
