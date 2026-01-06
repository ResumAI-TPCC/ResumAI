/**
 * API Utility Functions - Connect to Backend Server
 * 
 * RA-22: Upload Logic with progress tracking
 * Based on Design Doc: 4.2.1 Upload & Parse Resume
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Upload resume file to backend with progress tracking
 * 
 * Endpoint: POST /api/resumes
 * Request: multipart/form-data with 'file' field
 * Response: { status, data: { sid, timestamp, expireAt } }
 * 
 * @param {File} file - The resume file to upload (PDF, DOCX, DOC, TXT, max 5MB)
 * @param {function} onProgress - Optional progress callback (0-100)
 * @returns {Promise<Object>} - Response with sid and metadata
 */
export async function uploadResume(file, onProgress = null) {
  const formData = new FormData();
  formData.append('file', file);

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          onProgress(percentComplete);
        }
      });
    }

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new Error('Invalid response format'));
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          reject(new Error(errorData.detail || `Upload failed: ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.status}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener('error', () => {
      reject(new Error('Network error occurred'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'));
    });

    // Send request to /api/resumes (per design doc)
    xhr.open('POST', `${API_BASE_URL}/resumes`);
    xhr.send(formData);
  });
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
