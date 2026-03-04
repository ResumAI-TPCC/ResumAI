/**
 * Storage Utility Functions - Session Management
 * 
 * Based on Design Doc: Session-Based Data
 * Uses 'session_id' as per API specification
 */

const STORAGE_KEY = 'resumai_session';

/**
 * Session data structure (per design doc)
 * @typedef {Object} SessionData
 * @property {string} session_id - Session ID from backend (UUID)
 * @property {string} [expire_at] - Session expiration time
 * @property {string} [companyName] - Target company name
 * @property {string} [jobTitle] - Target job title
 * @property {string} [jobDescription] - Job description
 */

/**
 * Save session data to localStorage
 * @param {SessionData} sessionData - Session data to save
 * @returns {boolean} - Success status
 */
export function saveSession(sessionData) {
  try {
    const data = {
      ...sessionData,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error('Failed to save session:', error);
    return false;
  }
}

/**
 * Load session data from localStorage
 * @returns {SessionData|null} - Session data or null if not found/expired
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
 * @returns {boolean} - Success status
 */
export function clearSession() {
  try {
    localStorage.clear();
    return true;
  } catch (error) {
    console.error('Failed to clear session:', error);
    return false;
  }
}
