/**
 * Environment Configuration
 * 
 * Centralized environment variable management for the frontend application.
 * All environment variables should be imported from this file.
 */

export const ENV = {
  // API Configuration
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  
  // Application Metadata
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '0.1.0',
}

// Readonly to prevent accidental mutations
Object.freeze(ENV)
