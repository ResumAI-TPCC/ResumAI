/**
 * API Utility Functions - Connect to Backend Server
 * 
 * RA-22: Upload Logic with progress tracking
 * Based on Design Doc: 4.2.1 Upload & Parse Resume
 * 
 * Enhanced with:
 * - Timeout control (60 seconds)
 * - AbortController support for cancellation
 * - Better error classification
 *
 * RA-82: LLM endpoints (/analyze, /match, /optimize) return a job_id
 * immediately (202 Accepted). Callers use pollJobResult() to wait for
 * completion. The three public functions encapsulate submit + poll internally.
 */

import { ENV } from '../config/env.js'

const API_BASE_URL = ENV.API_BASE_URL;
const DEFAULT_TIMEOUT = 60000; // 60 seconds

// RA-82: Polling configuration
const POLL_INTERVAL_MS = 2000;   // check every 2 seconds
const POLL_TIMEOUT_MS  = 120000; // give up after 2 minutes

/**
 * Custom error class for API errors with classification
 */
export class ApiError extends Error {
  constructor(message, type = 'UNKNOWN_ERROR', originalError = null) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.originalError = originalError;
  }
}

/**
 * Error types for classification
 */
export const ErrorTypes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  CLIENT_ERROR: 'CLIENT_ERROR',
  CANCELLED: 'CANCELLED',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
};

/**
 * Create a timeout promise that rejects after specified milliseconds
 * @param {number} ms - Timeout in milliseconds
 * @param {AbortController} controller - AbortController to cancel the request
 * @returns {Promise} - Promise that rejects on timeout
 */
function createTimeoutPromise(ms, controller) {
  return new Promise((_, reject) => {
    const timeoutId = setTimeout(() => {
      controller.abort();
      reject(new ApiError(
        `Request timed out after ${ms / 1000} seconds`,
        ErrorTypes.TIMEOUT_ERROR
      ));
    }, ms);

    // Clear timeout if controller is aborted externally
    controller.signal.addEventListener('abort', () => {
      clearTimeout(timeoutId);
    });
  });
}

/**
 * Wrap fetch with timeout and abort support
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @param {AbortController} controller - AbortController for cancellation
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>} - Fetch response
 */
async function fetchWithTimeout(url, options, controller, timeout = DEFAULT_TIMEOUT) {
  const fetchPromise = fetch(url, {
    ...options,
    signal: controller.signal,
  });

  return Promise.race([
    fetchPromise,
    createTimeoutPromise(timeout, controller),
  ]);
}

/**
 * Handle HTTP response and extract error information
 * @param {Response} response - Fetch response object
 * @returns {Promise<void>} - Throws error if response is not ok
 */
async function handleErrorResponse(response) {
  let errorData;
  try {
    errorData = await response.json();
  } catch {
    errorData = { detail: `HTTP error: ${response.status}` };
  }

  const errorMessage = errorData.detail || errorData.message || `Request failed with status ${response.status}`;

  if (response.status >= 500) {
    throw new ApiError(errorMessage, ErrorTypes.SERVER_ERROR);
  }
  
  if (response.status >= 400) {
    throw new ApiError(errorMessage, ErrorTypes.CLIENT_ERROR);
  }

  throw new ApiError(errorMessage, ErrorTypes.UNKNOWN_ERROR);
}

/**
 * Map fetch/abort errors to ApiError and throw
 * @param {Error} error - Original error
 * @param {string} fallbackMessage - Message for unknown errors
 * @throws {ApiError}
 */
function handleFetchError(error, fallbackMessage) {
  if (error instanceof ApiError) {
    throw error;
  }

  if (error.name === 'AbortError') {
    throw new ApiError('Request cancelled', ErrorTypes.CANCELLED);
  }

  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    throw new ApiError('Network error. Please check your internet connection.', ErrorTypes.NETWORK_ERROR);
  }

  throw new ApiError(fallbackMessage, ErrorTypes.UNKNOWN_ERROR, error);
}

/**
 * @param {number} ms
 * @param {AbortSignal} [signal]
 * @returns {Promise<void>}
 */
function sleep(ms, signal = null) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new ApiError('Request cancelled', ErrorTypes.CANCELLED));
      return;
    }

    const timeoutId = setTimeout(resolve, ms);

    if (signal) {
      signal.addEventListener('abort', () => {
        clearTimeout(timeoutId);
        reject(new ApiError('Request cancelled', ErrorTypes.CANCELLED));
      }, { once: true });
    }
  });
}

/**
 * Poll GET /jobs/{jobId} until the job reaches a terminal state.
 *
 * @param {string} jobId - The job_id returned by a submit endpoint
 * @param {AbortController} [controller] - Optional AbortController for cancellation
 * @returns {Promise<Object>} The `result` payload from the completed job
 * @throws {ApiError} On job failure, timeout, or network error
 */
async function pollJobResult(jobId, controller = null) {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  const signal = controller?.signal ?? null;

  while (Date.now() < deadline) {
    if (signal?.aborted) {
      throw new ApiError('Request cancelled', ErrorTypes.CANCELLED);
    }

    await sleep(POLL_INTERVAL_MS, signal);

    try {
      const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, { signal });

      if (res.status === 404) {
        throw new ApiError('Job not found or result has expired. Please try again.', ErrorTypes.CLIENT_ERROR);
      }
      if (!res.ok) {
        throw new ApiError(`Polling error: ${res.status}`, ErrorTypes.SERVER_ERROR);
      }

      const body = await res.json();
      const { status, result, error } = body?.data ?? {};

      if (status === 'completed') {
        return result;
      }
      if (status === 'failed') {
        throw new ApiError(error || 'Job processing failed. Please try again.', ErrorTypes.SERVER_ERROR);
      }
      // status === 'pending' or 'processing' — keep polling
    } catch (error) {
      handleFetchError(error, `Polling error for job ${jobId}`);
    }
  }

  throw new ApiError(
    'Request timed out. The server is taking too long. Please try again.',
    ErrorTypes.TIMEOUT_ERROR
  );
}

/**
 * Upload resume file to backend with progress tracking
 * 
 * Endpoint: POST /api/resumes
 * Request: multipart/form-data with 'file' field
 * Response: { status, data: { sid, timestamp, expireAt } }
 * 
 * @param {File} file - The resume file to upload (PDF, DOCX, max 10MB)
 * @param {function} onProgress - Optional progress callback (0-100)
 * @param {AbortController} externalController - Optional external AbortController
 * @returns {Promise<Object>} - Response with sid and metadata
 */
export async function uploadResume(file, onProgress = null, externalController = null) {
  const formData = new FormData();
  formData.append('file', file);

  // Use external controller if provided
  // Note: XMLHttpRequest doesn't use AbortController directly
  // We handle abort through event listeners instead

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    // Set up timeout
    const timeoutId = setTimeout(() => {
      xhr.abort();
      reject(new ApiError(
        `Upload timed out after ${DEFAULT_TIMEOUT / 1000} seconds`,
        ErrorTypes.TIMEOUT_ERROR
      ));
    }, DEFAULT_TIMEOUT);

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
      clearTimeout(timeoutId);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new ApiError('Invalid response format', ErrorTypes.SERVER_ERROR));
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          reject(new ApiError(
            errorData.detail || `Upload failed: ${xhr.status}`,
            xhr.status >= 500 ? ErrorTypes.SERVER_ERROR : ErrorTypes.CLIENT_ERROR
          ));
        } catch {
          reject(new ApiError(
            `Upload failed: ${xhr.status}`,
            ErrorTypes.SERVER_ERROR
          ));
        }
      }
    });

    // Handle errors
    xhr.addEventListener('error', () => {
      clearTimeout(timeoutId);
      reject(new ApiError('Network error occurred', ErrorTypes.NETWORK_ERROR));
    });

    xhr.addEventListener('abort', () => {
      clearTimeout(timeoutId);
      reject(new ApiError('Upload cancelled', ErrorTypes.CANCELLED));
    });

    // Listen to external abort signal
    if (externalController) {
      externalController.signal.addEventListener('abort', () => {
        xhr.abort();
      });
    }

    // Send request to /api/resumes/ (trailing slash required by FastAPI router)
    xhr.open('POST', `${API_BASE_URL}/resumes/`);
    xhr.send(formData);
  });
}

/**
 * Analyze resume quality
 * @param {string} sessionId - Session ID
 * @param {AbortController} controller - Optional AbortController for cancellation
 * @returns {Promise<Object>} Analysis suggestions
 * @throws {ApiError} If sessionId is empty or API call fails
 */
export async function analyzeResume(sessionId, controller = null) {
  // Validate input
  if (!sessionId || typeof sessionId !== 'string' || sessionId.trim() === '') {
    throw new ApiError('Session ID is required and cannot be empty', ErrorTypes.VALIDATION_ERROR);
  }

  const internalController = controller || new AbortController();

  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/resumes/analyze`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId.trim() }),
      },
      internalController
    );

    // Handle different HTTP status codes
    if (response.status === 400) {
      const errorData = await response.json().catch(() => ({ detail: 'Invalid request' }));
      throw new ApiError(
        errorData.detail || errorData.message || 'Invalid request parameters',
        ErrorTypes.CLIENT_ERROR
      );
    }

    if (response.status === 404) {
      const errorData = await response.json().catch(() => ({ detail: 'Resume not found' }));
      throw new ApiError(
        errorData.detail || errorData.message || 'Resume not found. Please upload your resume again.',
        ErrorTypes.CLIENT_ERROR
      );
    }

    // Handle 422 Unprocessable Entity - file format incompatible for analysis
    if (response.status === 422) {
      throw new ApiError(
        'The file format is incompatible for analysis. Please use PDF or DOCX.',
        ErrorTypes.CLIENT_ERROR
      );
    }

    if (response.status === 429) {
      throw new ApiError('Server is busy. Please try again in a moment.', ErrorTypes.SERVER_ERROR);
    }

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    const submitResult = await response.json();
    const jobId = submitResult?.data?.job_id;
    if (!jobId) {
      throw new ApiError('Invalid response format from server', ErrorTypes.SERVER_ERROR);
    }

    const jobResult = await pollJobResult(jobId, internalController);
    return { status: 'ok', data: jobResult };
  } catch (error) {
    console.error('Unexpected error in analyzeResume:', error);
    handleFetchError(error, 'An unexpected error occurred. Please try again.');
  }
}

/**
 * Match resume with job description
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description text
 * @param {string} jobTitle - Job title (optional)
 * @param {string} companyName - Company name (optional)
 * @param {AbortController} controller - Optional AbortController for cancellation
 * @returns {Promise<Object>} Match score and suggestions
 */
export async function matchResumeWithJob(sessionId, jobDescription, jobTitle = '', companyName = '', controller = null) {
  const internalController = controller || new AbortController();

  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/resumes/match`,
      {
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
      },
      internalController
    );

    if (response.status === 429) {
      throw new ApiError('Server is busy. Please try again in a moment.', ErrorTypes.SERVER_ERROR);
    }

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    const submitResult = await response.json();
    const jobId = submitResult?.data?.job_id;
    if (!jobId) {
      throw new ApiError('Invalid response format from server', ErrorTypes.SERVER_ERROR);
    }

    const jobResult = await pollJobResult(jobId, internalController);
    return { status: 'ok', data: jobResult };
  } catch (error) {
    handleFetchError(error, 'Match request failed. Please try again.');
  }
}

/**
 * Optimize resume and generate file
 * @param {string} sessionId - Session ID
 * @param {string} jobDescription - Job description (optional)
 * @param {string} template - Template name (optional)
 * @param {AbortController} controller - Optional AbortController for cancellation
 * @returns {Promise<Object>} Encoded file data
 */
export async function optimizeResume(sessionId, jobDescription = '', template = 'modern', controller = null) {
  const internalController = controller || new AbortController();

  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/resumes/optimize`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          job_description: jobDescription,
          template,
        }),
      },
      internalController
    );

    if (response.status === 429) {
      throw new ApiError('Server is busy. Please try again in a moment.', ErrorTypes.SERVER_ERROR);
    }

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    const submitResult = await response.json();
    const jobId = submitResult?.data?.job_id;
    if (!jobId) {
      throw new ApiError('Invalid response format from server', ErrorTypes.SERVER_ERROR);
    }

    const jobResult = await pollJobResult(jobId, internalController);
    return { status: 'ok', data: jobResult };
  } catch (error) {
    handleFetchError(error, 'Optimization request failed. Please try again.');
  }
}
