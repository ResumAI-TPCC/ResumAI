import PropTypes from 'prop-types'

/**
 * ResumePreview Component
 * 
 * Displays:
 * - Match score (if available)
 * - Resume file preview and info
 * - Resume action buttons
 * 
 * RA-20: Optimize Resume UI Implementation
 */
function ResumePreview({ 
  uploadedFile, 
  matchScore, 
  isOptimizing, 
  isAnalyzing,
  isReanalyzing,
  optimizedData,
  actionsEnabled,
  onOptimize,
  onDownload,
  onReanalyze,
}) {
  const optimizedHtml = optimizedData?.optimized_html || ''
  const hasOptimizedFile = Boolean(optimizedData?.encoded_file)

  const getFileSizeInKB = (bytes) => {
    if (!bytes) return '0'
    return (bytes / 1024).toFixed(1)
  }

  const handleGenerate = () => onOptimize?.()

  const handleDownload = () => onDownload?.()

  const handleReanalyze = () => onReanalyze?.()

  return (
    <aside className="w-80 bg-white border-l border-gray-200 h-screen flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div>
          <h2 className="font-bold text-lg text-gray-800">Resume Preview</h2>
          <p className="text-xs text-gray-500">Document Preview</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {/* RA-59: Show loading skeleton while analyzing, real score when done */}
        {isAnalyzing ? (
          <div className="mb-4 rounded-lg bg-gradient-to-r from-indigo-500 via-purple-500 to-purple-600 p-4 text-white shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-white/90">Match Score</p>
                <div className="mt-2 flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" aria-label="Calculating score" />
                  <span className="text-sm font-medium text-white/80">Calculating...</span>
                </div>
              </div>
              <svg className="h-10 w-10 opacity-40" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-white/30">
              <div className="h-2 rounded-full bg-white/50 animate-pulse w-full" />
            </div>
          </div>
        ) : matchScore !== null && matchScore !== undefined ? (
          <div className="mb-4 rounded-lg bg-gradient-to-r from-indigo-500 via-purple-500 to-purple-600 p-4 text-white shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-white/90">Match Score</p>
                <div className="mt-1 flex items-baseline">
                  <span className="text-3xl font-bold">{matchScore}</span>
                  <span className="ml-1 text-base font-medium">/100</span>
                </div>
              </div>
              <svg className="h-10 w-10 opacity-70" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-white/30">
              <div
                className="h-2 rounded-full bg-white transition-all duration-500"
                style={{ width: `${matchScore}%` }}
              />
            </div>
          </div>
        ) : null}

        {optimizedHtml ? (
          <>
            <style>{`
              .resume-preview h1 { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; border-bottom: 2px solid #1a1a2e; padding-bottom: 4px; margin-bottom: 8px; text-align: center; }
              .resume-preview h2 { font-size: 1rem; font-weight: 600; color: #1a1a2e; border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; margin-top: 14px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
              .resume-preview h3 { font-size: 0.9rem; font-weight: 600; color: #333; margin-top: 8px; margin-bottom: 4px; }
              .resume-preview p { margin: 2px 0 6px 0; }
              .resume-preview ul { padding-left: 16px; margin: 2px 0; }
              .resume-preview li { margin-bottom: 2px; }
              .resume-preview strong { color: #1a1a2e; }
              .resume-preview em { color: #555; }
            `}</style>
            <div
              className="resume-preview text-sm text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: optimizedHtml }}
            />
          </>
        ) : (
          <div className="text-gray-400 text-center mt-8">
            <svg className="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm">Optimized resume will appear here after generation</p>
          </div>
        )}
      </div>

      <div className="p-4 space-y-6 border-t border-gray-200">
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

        <div className="space-y-3">
          <button
            onClick={handleGenerate}
            disabled={!actionsEnabled || isOptimizing}
            className="w-full px-4 py-3 bg-purple-600 text-white font-medium rounded-md hover:bg-purple-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isOptimizing ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                {optimizedData ? 'Regenerate Resume' : 'Generate Polished Resume'}
              </>
            )}
          </button>

          <button
            onClick={handleDownload}
            disabled={!actionsEnabled || !hasOptimizedFile}
            className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Polished Resume
          </button>

          <button
            onClick={handleReanalyze}
            disabled={!actionsEnabled || isAnalyzing}
            className="w-full px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-md hover:bg-gray-200 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isReanalyzing ? (
              <>
                <svg className="animate-spin h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Re-analyzing...</span>
              </>
            ) : (
              <span>Re-analyze</span>
            )}
          </button>

          {hasOptimizedFile && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-xs text-green-700 font-medium mb-2">Polished Resume Ready</p>
              <p className="text-xs text-green-600">Your optimized resume is ready to download</p>
            </div>
          )}
        </div>
      </div>

      {/* Info Text */}
      {!actionsEnabled && (
        <div className="text-xs text-gray-500 text-center p-3 bg-gray-50 rounded-md">
          Please upload a resume to get started
        </div>
      )}
    </aside>
  )
}

ResumePreview.propTypes = {
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  matchScore: PropTypes.number,
  isOptimizing: PropTypes.bool,
  isAnalyzing: PropTypes.bool,
  isReanalyzing: PropTypes.bool,
  actionsEnabled: PropTypes.bool,
  optimizedData: PropTypes.shape({
    encoded_file: PropTypes.string,
    optimized_html: PropTypes.string,
  }),
  onOptimize: PropTypes.func,
  onDownload: PropTypes.func,
  onReanalyze: PropTypes.func,
}

export default ResumePreview
