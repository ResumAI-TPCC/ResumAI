/**
 * Jest Test Setup
 * Configure global mocks and test environment
 */

import '@testing-library/jest-dom'

// Mock import.meta.env for Vite
Object.defineProperty(globalThis, 'import', {
  value: {
    meta: {
      env: {
        VITE_API_BASE_URL: 'http://localhost:8000/api'
      }
    }
  }
})
