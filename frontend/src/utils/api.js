/**
 * API Utility Functions - Connect to Backend Server
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Upload resume file to backend
 * @param {File} file - Resume file (PDF, DOCX, DOC, TXT)
 * @returns {Promise<Object>} Response with session_id and expire_at
 */
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/resumes`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Upload failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Analyze resume quality
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Analysis suggestions
 */
export async function analyzeResume(sessionId) {
  const response = await fetch(`${API_BASE_URL}/resumes/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Analysis failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Match resume with job description
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description text
 * @param {string} jobTitle - Job title (optional)
 * @param {string} companyName - Company name (optional)
 * @returns {Promise<Object>} Match score and suggestions
 */
export async function matchResumeWithJob(sessionId, jobDescription, jobTitle = '', companyName = '') {
  const response = await fetch(`${API_BASE_URL}/resumes/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      job_description: jobDescription,
      job_title: jobTitle,
      company_name: companyName,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Match failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

/**
 * Optimize resume and generate file
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description (optional)
 * @param {string} template - Template name (optional)
 * @returns {Promise<Object>} Encoded file data
 */
export async function optimizeResume(sessionId, jobDescription = '', template = 'modern') {
  const response = await fetch(`${API_BASE_URL}/resumes/optimize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      job_description: jobDescription,
      template,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Optimization failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
