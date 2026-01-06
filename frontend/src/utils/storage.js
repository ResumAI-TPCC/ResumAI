/**
 * Storage Utility Functions - Session Management
 * 
 * Based on Design Doc: Session-Based Data
 * Uses 'sid' (session ID) as per API specification
 */

const STORAGE_KEY = 'resumai_session';

/**
 * Session data structure (per design doc)
 * @typedef {Object} SessionData
 * @property {string} sid - Session ID from backend (UUID)
 * @property {string} fileName - Uploaded file name
 * @property {number} fileSize - File size in bytes
 * @property {string} timestamp - ISO timestamp from backend
 * @property {string} [expire_at] - Session expiration time
 * @property {string} [companyName] - Target company name
 * @property {string} [jobTitle] - Target job title
 * @property {string} [jobDescription] - Job description
 */

/**
 * Save session data to localStorage
 * @param {SessionData} sessionData - Session data to save
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
 */
export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (error) {
    console.error('Failed to clear session:', error);
    return false;
  }
}

/**
 * Check if a valid session exists
 * @returns {boolean}
 */
export function hasSession() {
  const session = loadSession();
  return session !== null && session.sid !== undefined;
}

/**
 * Get session ID (sid) if exists
 * @returns {string|null}
 */
export function getSessionId() {
  const session = loadSession();
  return session?.sid || null;
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
