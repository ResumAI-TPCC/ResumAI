/**
 * API Utility Functions - Connect to Backend Server
 * 
 * RA-22: Upload Logic with progress tracking
 * Based on Design Doc: 4.2.1 Upload & Parse Resume
 *
 * RA-82: LLM endpoints (/analyze, /match, /optimize) now return a job_id
 * immediately (202 Accepted). Callers use pollJobResult() to wait for
 * completion. The three public functions (analyzeResume, matchResumeWithJob,
 * optimizeResume) encapsulate submit + poll internally so all existing
 * call-sites remain unchanged.
 */

import { ENV } from '../config/env.js'

const API_BASE_URL = ENV.API_BASE_URL;

// RA-82: Polling configuration
const POLL_INTERVAL_MS = 2000;   // check every 2 seconds
const POLL_TIMEOUT_MS  = 120000; // give up after 2 minutes

/**
 * Upload resume file to backend with progress tracking
 * 
 * Endpoint: POST /api/resumes
 * Request: multipart/form-data with 'file' field
 * Response: { status, data: { sid, timestamp, expireAt } }
 * 
 * @param {File} file - The resume file to upload (PDF, DOCX, max 10MB)
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

    // Send request to /api/resumes/ (trailing slash required by FastAPI router)
    xhr.open('POST', `${API_BASE_URL}/resumes/`);
    xhr.send(formData);
  });
}

/**
 * Analyze resume quality
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Analysis suggestions  (same shape as before RA-82)
 * @throws {Error} If sessionId is empty or API call fails
 */
export async function analyzeResume(sessionId) {
  // Validate input
  if (!sessionId || typeof sessionId !== 'string' || sessionId.trim() === '') {
    throw new Error('Session ID is required and cannot be empty');
  }

  try {
    // RA-82: submit job, get job_id
    const response = await fetch(`${API_BASE_URL}/resumes/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId.trim() }),
    });

    if (response.status === 400) {
      const errorData = await response.json().catch(() => ({ detail: 'Invalid request' }));
      throw new Error(errorData.detail || errorData.message || 'Invalid request parameters');
    }
    if (response.status === 404) {
      const errorData = await response.json().catch(() => ({ detail: 'Resume not found' }));
      throw new Error(errorData.detail || errorData.message || 'Resume not found. Please upload your resume again.');
    }
    if (response.status === 422) {
      throw new Error('The file format is incompatible for analysis. Please use PDF or DOCX.');
    }
    if (response.status === 429) {
      throw new Error('Server is busy. Please try again in a moment.');
    }
    if (response.status === 500) {
      const errorData = await response.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(errorData.detail || errorData.message || 'Server error occurred. Please try again later.');
    }
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(errorData.detail || errorData.message || `Analysis failed: ${response.status}`);
    }

    const submitResult = await response.json();
    const jobId = submitResult?.data?.job_id;
    if (!jobId) throw new Error('Invalid response format from server');

    // RA-82: poll until completed, then return in the original shape
    // { status: 'ok', data: { suggestions: [...] } }
    const jobResult = await pollJobResult(jobId);
    return { status: 'ok', data: jobResult };

  } catch (error) {
    if (error.message.includes('Session ID is required') ||
      error.message.includes('Resume not found') ||
      error.message.includes('Invalid request') ||
      error.message.includes('Server error') ||
      error.message.includes('file format is incompatible') ||
      error.message.includes('rejected') ||
      error.message.includes('moderation') ||
      error.message.includes('Server is busy')) {
      throw error;
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error. Please check your internet connection.');
    }
    console.error('Unexpected error in analyzeResume:', error);
    throw new Error('An unexpected error occurred. Please try again.');
  }
}

/**
 * Match resume with job description
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description text
 * @param {string} jobTitle - Job title (optional)
 * @param {string} companyName - Company name (optional)
 * @returns {Promise<Object>} Match score and suggestions  (same shape as before RA-82)
 */
export async function matchResumeWithJob(sessionId, jobDescription, jobTitle = '', companyName = '') {
  // RA-82: submit job
  const response = await fetch(`${API_BASE_URL}/resumes/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      job_description: jobDescription,
      job_title: jobTitle,
      company_name: companyName,
    }),
  });

  if (response.status === 429) {
    throw new Error('Server is busy. Please try again in a moment.');
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Match failed' }));
    throw new Error(error.detail || error.message || `HTTP error! status: ${response.status}`);
  }

  const submitResult = await response.json();
  const jobId = submitResult?.data?.job_id;
  if (!jobId) throw new Error('Invalid response format from server');

  // RA-82: poll, then wrap in original shape
  // { status: 'ok', data: { match_score, match_breakdown, suggestions } }
  const jobResult = await pollJobResult(jobId);
  return { status: 'ok', data: jobResult };
}

/**
 * Optimize resume and generate file
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description (optional)
 * @param {string} template - Template name (optional)
 * @returns {Promise<Object>} Encoded file data  (same shape as before RA-82)
 */
export async function optimizeResume(sessionId, jobDescription = '', template = 'modern') {
  // RA-82: submit job
  const response = await fetch(`${API_BASE_URL}/resumes/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      job_description: jobDescription,
      template,
    }),
  });

  if (response.status === 429) {
    throw new Error('Server is busy. Please try again in a moment.');
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Optimization failed' }));
    throw new Error(error.detail || error.message || `HTTP error! status: ${response.status}`);
  }

  const submitResult = await response.json();
  const jobId = submitResult?.data?.job_id;
  if (!jobId) throw new Error('Invalid response format from server');

  // RA-82: poll, then wrap in original shape
  // { status: 'ok', data: { encoded_file: '...' } }
  const jobResult = await pollJobResult(jobId);
  return { status: 'ok', data: jobResult };
}

/**
 * Poll GET /jobs/{jobId} until the job reaches a terminal state.
 *
 * @param {string} jobId - The job_id returned by a submit endpoint
 * @returns {Promise<Object>} The `result` payload from the completed job
 * @throws {Error} On job failure, timeout, or network error
 */
async function pollJobResult(jobId) {
  const deadline = Date.now() + POLL_TIMEOUT_MS;

  while (Date.now() < deadline) {
    await sleep(POLL_INTERVAL_MS);

    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);

    if (res.status === 404) {
      throw new Error('Job not found or result has expired. Please try again.');
    }
    if (!res.ok) {
      throw new Error(`Polling error: ${res.status}`);
    }

    const body = await res.json();
    const { status, result, error } = body?.data ?? {};

    if (status === 'completed') {
      return result;
    }
    if (status === 'failed') {
      throw new Error(error || 'Job processing failed. Please try again.');
    }
    // status === 'pending' or 'processing' — keep polling
  }

  throw new Error('Request timed out. The server is taking too long. Please try again.');
}

/**
 * @param {number} ms
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
