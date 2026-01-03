/**
 * API Utility Functions - Resume Upload
 * 
 * RA-22: Upload Logic Implementation
 * Based on Design Doc: 4.2.1 Upload & Parse Resume
 */

// API Base URL - defaults to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

/**
 * Upload resume file to backend
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
  const formData = new FormData()
  formData.append('file', file)

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100)
          onProgress(percentComplete)
        }
      })
    }

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText)
          resolve(response)
        } catch (e) {
          reject(new Error('Invalid response format'))
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText)
          reject(new Error(errorData.detail || `Upload failed: ${xhr.status}`))
        } catch (e) {
          reject(new Error(`Upload failed: ${xhr.status}`))
        }
      }
    })

    // Handle errors
    xhr.addEventListener('error', () => {
      reject(new Error('Network error occurred'))
    })

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'))
    })

    // Send request to /api/resumes (per design doc)
    xhr.open('POST', `${API_BASE_URL}/resumes`)
    xhr.send(formData)
  })
}

// TODO: Other API functions to be implemented by respective owners
// - analyzeResume() -> POST /api/resumes/{id}/analyze
// - matchResumeWithJob() -> POST /api/resumes/{id}/match
// - optimizeResume() -> POST /api/resumes/{id}/optimize
