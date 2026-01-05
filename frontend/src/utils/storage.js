/**
 * Storage Utility Functions - Session Management
 */

const STORAGE_KEY = 'resumai_session';

/**
 * Save session data to localStorage
 * @param {Object} sessionData - Session data object
 */
export function saveSession(sessionData) {
  try {
    const data = {
      ...sessionData,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save session:', error);
  }
}

/**
 * Load session data from localStorage
 * @returns {Object|null} Session data or null if not found
 */
export function loadSession() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return null;

    const sessionData = JSON.parse(data);
    
    // Check if session is expired
    if (sessionData.expire_at) {
      const expireTime = new Date(sessionData.expire_at);
      const now = new Date();
      if (now > expireTime) {
        clearSession();
        return null;
      }
    }

    return sessionData;
  } catch (error) {
    console.error('Failed to load session:', error);
    return null;
  }
}

/**
 * Clear session data from localStorage
 */
export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear session:', error);
  }
}

/**
 * Update specific session field
 * @param {string} key - Field name
 * @param {*} value - Field value
 */
export function updateSessionField(key, value) {
  const session = loadSession() || {};
  session[key] = value;
  saveSession(session);
}

/**
 * Get session field value
 * @param {string} key - Field name
 * @returns {*} Field value or null
 */
export function getSessionField(key) {
  const session = loadSession();
  return session ? session[key] : null;
}
