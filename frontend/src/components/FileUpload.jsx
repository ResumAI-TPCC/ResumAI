import { useState, useRef, useCallback } from 'react'
import PropTypes from 'prop-types'

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
const ACCEPTED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain'
]

function FileUpload({ onFileSelect, uploadedFile, onRemoveFile }) {
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

  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.pdf')) {
      return (
        <svg className="w-12 h-12 text-red-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
        </svg>
      )
    } else if (fileName.endsWith('.docx') || fileName.endsWith('.doc')) {
      return (
        <svg className="w-12 h-12 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
        </svg>
      )
    } else {
      return (
        <svg className="w-12 h-12 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
        </svg>
      )
    }
  }

  // If file is uploaded, show file info card
  if (uploadedFile) {
    return (
      <div className="animate-fade-in">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 hover:shadow-xl transition-shadow">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              {getFileIcon(uploadedFile.name)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                    {uploadedFile.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(uploadedFile.size)}
                  </p>
                </div>
                <button
                  onClick={onRemoveFile}
                  className="flex-shrink-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Remove file"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium">File selected, ready to analyze</span>
                </div>
              </div>
            </div>
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
          relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50 scale-[1.02]' 
            : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/50'
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
            w-20 h-20 rounded-full flex items-center justify-center mb-6
            transition-colors duration-200
            ${isDragging 
              ? 'bg-blue-100' 
              : 'bg-gray-100'
            }
          `}>
            <svg 
              className={`w-10 h-10 transition-colors duration-200 ${
                isDragging ? 'text-blue-600' : 'text-gray-400'
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
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {isDragging ? 'Release to upload file' : 'Drag and drop file here or click to upload'}
          </h3>
          <p className="text-sm text-gray-500 mb-1">
            Supports PDF, DOCX, DOC, TXT formats
          </p>
          <p className="text-xs text-gray-400">
            Maximum file size: 5MB
          </p>

          {/* Upload Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              handleClick()
            }}
            className="mt-6 px-6 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
          >
            Select File
          </button>
        </div>

        {/* Drag Overlay */}
        {isDragging && (
          <div className="absolute inset-0 bg-blue-500/10 rounded-2xl pointer-events-none" />
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl animate-fade-in">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-700">{error}</p>
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
  onRemoveFile: PropTypes.func.isRequired,
}

FileUpload.defaultProps = {
  uploadedFile: null,
}

export default FileUpload
