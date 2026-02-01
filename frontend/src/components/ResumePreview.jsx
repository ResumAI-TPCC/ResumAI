import { useState } from 'react'
import PropTypes from 'prop-types'

/**
 * ResumePreview Component
 * 
 * Displays:
 * - Match score (if available)
 * - Resume file preview and info
 * - Toggle for generating polished resume
 * - Download button for optimized resume
 * 
 * RA-20: Optimize Resume UI Implementation
 */
function ResumePreview({ 
  sessionId, 
  uploadedFile, 
  matchScore, 
  isOptimizing, 
  optimizedFile,
  onOptimize,
  onDownload 
}) {
  const [isGenerateToggled, setIsGenerateToggled] = useState(false)

  // Props validation
  void sessionId

  const getFileSizeInKB = (bytes) => {
    if (!bytes) return '0'
    return (bytes / 1024).toFixed(1)
  }

  const handleToggleGenerate = () => {
    setIsGenerateToggled(!isGenerateToggled)
    if (!isGenerateToggled) {
      onOptimize?.()
    }
  }

  const handleDownload = () => {
    onDownload?.()
  }

  return (
    <aside className="w-80 bg-white border-l border-gray-200 p-6 h-screen overflow-y-auto flex flex-col">
      {/* Header: Title + small match badge */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="font-bold text-lg text-gray-800">Resume Preview</p>
          <p className="text-xs text-gray-500">Document Preview</p>
        </div>
        {matchScore !== null && matchScore !== undefined ? (
          <div className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
            {matchScore}/100
          </div>
        ) : (
          <div className="text-xs text-gray-400">&nbsp;</div>
        )}
      </div>

      <div className="flex-1 space-y-6">
        {/* Resume File Preview Card */}
        <div className="bg-white rounded-lg shadow p-6">
          {uploadedFile ? (
            <div className="flex flex-col items-center">
              <div className="w-20 h-20 bg-blue-50 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="font-semibold text-gray-900 text-sm truncate mb-1">{uploadedFile.name}</p>
              <p className="text-xs text-gray-500 mb-3">Document Preview (Mock)</p>
              <div className="w-full bg-gray-50 rounded-md p-3 text-center">
                <p className="text-xs text-gray-600">File Size: {getFileSizeInKB(uploadedFile.size)} KB</p>
              </div>
            </div>
          ) : (
            <div className="text-center text-sm text-gray-500">Please upload a resume to preview</div>
          )}
        </div>

        {/* Generate Polished Resume Section */}
        <div className="border-t border-gray-200 pt-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">
              Generate Polished Resume
            </span>
            <button
              onClick={handleToggleGenerate}
              disabled={!sessionId || isOptimizing}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isGenerateToggled 
                  ? 'bg-blue-600' 
                  : 'bg-gray-300'
              } ${!sessionId || isOptimizing ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isGenerateToggled ? 'translate-x-5' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Loading State for Optimization */}
          {isOptimizing && (
            <div className="flex items-center justify-center py-4">
              <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="ml-2 text-sm text-gray-600">Generating...</span>
            </div>
          )}

          {/* Optimized File Info */}
          {optimizedFile && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-xs text-green-700 font-medium mb-2">? Polished Resume Ready</p>
              <p className="text-xs text-green-600">
                Your optimized resume is ready to download
              </p>
            </div>
          )}
        </div>

        {/* Download Button */}
        <div className="border-t border-gray-200 pt-6 pb-4">
          <button
            onClick={handleDownload}
            disabled={!optimizedFile || !isGenerateToggled || !sessionId}
            className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Polished Resume
          </button>
        </div>
      </div>

      {/* Info Text */}
      {!sessionId && (
        <div className="text-xs text-gray-500 text-center p-3 bg-gray-50 rounded-md">
          Please upload a resume to get started
        </div>
      )}
    </aside>
  )
}

ResumePreview.propTypes = {
  sessionId: PropTypes.string,
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  matchScore: PropTypes.number,
  isOptimizing: PropTypes.bool,
  optimizedFile: PropTypes.shape({
    name: PropTypes.string,
    content: PropTypes.string,
  }),
  onOptimize: PropTypes.func,
  onDownload: PropTypes.func,
}

export default ResumePreview
