/**
 * useUpload Hook - Handle file upload logic
 * 
 * RA-22: Upload Logic Implementation
 * Based on Design Doc: 4.2.1 Upload & Parse Resume
 */

import { useState, useCallback } from 'react'
import { uploadResume } from '../utils/api'
import { saveSession, clearSession } from '../utils/storage'

/**
 * Upload states
 */
export const UploadStatus = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  SUCCESS: 'success',
  ERROR: 'error',
}

/**
 * Custom hook for handling resume upload
 * @returns {Object} Upload state and handlers
 */
export function useUpload() {
  const [status, setStatus] = useState(UploadStatus.IDLE)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  /**
   * Upload file to backend
   * 
   * Expected response format (per design doc):
   * {
   *   "status": "success",
   *   "data": {
   *     "sid": "uuid",
   *     "timestamp": "2024-01-15T10:30:00Z",
   *     "expireAt": "..."
   *   }
   * }
   * 
   * @param {File} file - File to upload
   * @returns {Promise<Object|null>} - Upload result or null on error
   */
  const upload = useCallback(async (file) => {
    setStatus(UploadStatus.UPLOADING)
    setProgress(0)
    setError(null)
    setResult(null)

    try {
      const response = await uploadResume(file, (percent) => {
        setProgress(percent)
      })

      // Extract data from response (per design doc structure)
      const { data } = response

      // Save session data
      saveSession({
        sid: data.sid,
        fileName: file.name,
        fileSize: file.size,
        timestamp: data.timestamp,
        expireAt: data.expireAt,
      })

      setResult(response)
      setStatus(UploadStatus.SUCCESS)
      setProgress(100)

      return response
    } catch (err) {
      const errorMessage = err.message || 'Upload failed'
      setError(errorMessage)
      setStatus(UploadStatus.ERROR)
      return null
    }
  }, [])

  /**
   * Reset upload state
   */
  const reset = useCallback(() => {
    setStatus(UploadStatus.IDLE)
    setProgress(0)
    setError(null)
    setResult(null)
    clearSession()
  }, [])

  /**
   * Clear error and retry
   */
  const clearError = useCallback(() => {
    setError(null)
    setStatus(UploadStatus.IDLE)
  }, [])

  return {
    // State
    status,
    progress,
    error,
    result,

    // Computed
    isIdle: status === UploadStatus.IDLE,
    isUploading: status === UploadStatus.UPLOADING,
    isSuccess: status === UploadStatus.SUCCESS,
    isError: status === UploadStatus.ERROR,

    // Actions
    upload,
    reset,
    clearError,
  }
}

export default useUpload
