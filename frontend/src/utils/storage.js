/**
 * Storage Utility Functions - Session Management
 * 
 * Based on Design Doc: Session-Based Data
 * Uses 'sid' (session ID) as per API specification
 */

const STORAGE_KEY = 'resumai_session'

/**
 * Session data structure (per design doc)
 * @typedef {Object} SessionData
 * @property {string} sid - Session ID from backend (UUID)
 * @property {string} fileName - Uploaded file name
 * @property {number} fileSize - File size in bytes
 * @property {string} timestamp - ISO timestamp from backend
 * @property {string} [expireAt] - Session expiration time
 * @property {string} [companyName] - Target company name
 * @property {string} [jobTitle] - Target job title
 * @property {string} [jobDescription] - Job description
 */

/**
 * Save session data to localStorage
 * @param {SessionData} data - Session data to save
 */
export function saveSession(data) {
  try {
    const existing = loadSession() || {}
    const updated = { ...existing, ...data }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    return true
  } catch (e) {
    console.error('Failed to save session:', e)
    return false
  }
}

/**
 * Load session data from localStorage
 * @returns {SessionData|null} - Session data or null if not found
 */
export function loadSession() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : null
  } catch (e) {
    console.error('Failed to load session:', e)
    return null
  }
}

/**
 * Clear session data from localStorage
 */
export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEY)
    return true
  } catch (e) {
    console.error('Failed to clear session:', e)
    return false
  }
}

/**
 * Check if a valid session exists
 * @returns {boolean}
 */
export function hasSession() {
  const session = loadSession()
  return session !== null && session.sid !== undefined
}

/**
 * Get session ID (sid) if exists
 * @returns {string|null}
 */
export function getSessionId() {
  const session = loadSession()
  return session?.sid || null
}

/**
 * Update specific fields in session
 * @param {Partial<SessionData>} updates - Fields to update
 */
export function updateSession(updates) {
  const session = loadSession()
  if (session) {
    saveSession({ ...session, ...updates })
  }
}
