import { useState, useRef, useCallback } from 'react'
import PropTypes from 'prop-types'

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
const ACCEPTED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain'
]

function FileUpload({ onFileSelect, uploadedFile, isUploaded = false, onRemoveFile }) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const validateFile = useCallback((file) => {
    // Check file type
    const isValidType = ACCEPTED_TYPES.includes(file.type) || 
                       file.name.endsWith('.pdf') ||
                       file.name.endsWith('.docx') ||
                       file.name.endsWith('.doc') ||
                       file.name.endsWith('.txt')

    if (!isValidType) {
      return { valid: false, error: 'Unsupported file format. Please upload PDF, DOCX, DOC, or TXT files.' }
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, error: 'File size exceeds 5MB limit. Please upload a smaller file.' }
    }

    return { valid: true, error: null }
  }, [])

  const handleFile = useCallback((file) => {
    const result = validateFile(file)
    setError(result.error)
    if (result.valid) {
      onFileSelect(file)
    }
  }, [onFileSelect, validateFile])

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleFileInput = (e) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
    // Reset input to allow selecting the same file
    e.target.value = ''
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  // If file is uploaded/selected, show file info card with green checkmark (only if uploaded)
  if (uploadedFile) {
    return (
      <div className="animate-fade-in">
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <div className="flex items-center gap-2.5">
            <div className="flex-shrink-0">
              {isUploaded ? (
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {uploadedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {formatFileSize(uploadedFile.size)}
              </p>
            </div>
            <button
              onClick={onRemoveFile}
              className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
              title="Remove file"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Upload area
  return (
    <div className="animate-fade-in">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-all duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.doc,.txt"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex flex-col items-center">
          {/* Upload Icon */}
          <div className={`
            w-12 h-12 rounded-full flex items-center justify-center mb-3
            transition-colors duration-200
            ${isDragging 
              ? 'bg-blue-100' 
              : 'bg-gray-200'
            }
          `}>
            <svg 
              className={`w-6 h-6 transition-colors duration-200 ${
                isDragging ? 'text-blue-600' : 'text-gray-500'
              }`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
              />
            </svg>
          </div>

          {/* Text Content */}
          <p className="text-sm text-gray-600 mb-1">
            {isDragging ? 'Release to upload file' : 'Click to upload or drag and drop'}
          </p>
          <p className="text-xs text-gray-500">
            PDF, DOCX, DOC, TXT (Max 5MB)
          </p>
        </div>

        {/* Drag Overlay */}
        {isDragging && (
          <div className="absolute inset-0 bg-blue-500/10 rounded-lg pointer-events-none" />
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg animate-fade-in">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-red-700">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}

FileUpload.propTypes = {
  onFileSelect: PropTypes.func.isRequired,
  uploadedFile: PropTypes.shape({
    name: PropTypes.string.isRequired,
    size: PropTypes.number.isRequired,
  }),
  isUploaded: PropTypes.bool,
  onRemoveFile: PropTypes.func.isRequired,
}

FileUpload.defaultProps = {
  uploadedFile: null,
  isUploaded: false,
}

export default FileUpload
