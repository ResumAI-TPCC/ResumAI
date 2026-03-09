import PropTypes from 'prop-types'
import FileUpload from './FileUpload'

function Sidebar({ 
  companyName, 
  jobTitle, 
  jobDescription, 
  selectedFile,
  uploadedFile,
  isUploading,
  isAnalyzing,
  isAnalyzeLoading,
  uploadError,
  canAnalyze,
  onCompanyNameChange,
  onJobTitleChange,
  onJobDescriptionChange,
  onFileSelect,
  onRemoveFile,
  onUpload,
  onAnalyze,
  onClearSession 
}) {
  const handleClearJD = () => {
    onJobDescriptionChange('')
  }

  const displayFile = uploadedFile || selectedFile

  return (
    <aside className="w-96 bg-white border-r border-gray-200 h-screen flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="p-5 space-y-4">
          {/* Header with Logo */}
          <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 leading-tight">
                ResumAI
              </h1>
              <p className="text-xs text-gray-600 leading-tight">
                Intelligent Resume Optimizer
              </p>
            </div>
          </div>

          {/* Company Name Input */}
          <div>
            <label htmlFor="company-name" className="block text-xs font-medium text-gray-700 mb-1.5">
              Company Name
            </label>
            <input
              id="company-name"
              type="text"
              value={companyName || ''}
              onChange={(e) => onCompanyNameChange(e.target.value)}
              placeholder="Enter company name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Job Title Input */}
          <div>
            <label htmlFor="job-title" className="block text-xs font-medium text-gray-700 mb-1.5">
              Job Title
            </label>
            <input
              id="job-title"
              type="text"
              value={jobTitle || ''}
              onChange={(e) => onJobTitleChange(e.target.value)}
              placeholder="Enter job title"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Job Description Textarea */}
          <div>
            <label htmlFor="job-description" className="block text-xs font-medium text-gray-700 mb-1.5">
              Job Description (JD)
            </label>
            <textarea
              id="job-description"
              value={jobDescription || ''}
              onChange={(e) => onJobDescriptionChange(e.target.value)}
              placeholder="(Optional) Paste job description here..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
            />
            {jobDescription && (
              <button
                onClick={handleClearJD}
                className="mt-1.5 text-xs text-gray-600 hover:text-gray-900 underline"
              >
                Clear JD
              </button>
            )}
          </div>

          {/* Resume Upload Section */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">
              Resume Upload <span className="text-red-500">*</span>
            </label>
            <FileUpload
              onFileSelect={onFileSelect}
              uploadedFile={displayFile}
              isUploaded={!!uploadedFile}
              onRemoveFile={onRemoveFile}
            />
            
            {/* Upload Button - Only show when file is selected but not uploaded yet */}
            {selectedFile && !uploadedFile && (
              <button
                onClick={onUpload}
                disabled={isUploading}
                className="mt-3 w-full px-4 py-2.5 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span>Upload</span>
                  </>
                )}
              </button>
            )}

            {/* Error Message */}
            {uploadError && (
              <div className="mt-3 p-2.5 bg-red-50 border border-red-200 rounded-md">
                <p className="text-xs text-red-700">{uploadError}</p>
              </div>
            )}
          </div>

          <div>
            <button
              onClick={onAnalyze}
              disabled={!canAnalyze || isAnalyzing}
              className="w-full px-4 py-2.5 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isAnalyzeLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{jobDescription && jobDescription.trim() ? 'Matching Resume...' : 'Analyzing Resume...'}</span>
                </>
              ) : (
                <span>{jobDescription && jobDescription.trim() ? 'Match Resume' : 'Analyze Resume'}</span>
              )}
            </button>
          </div>

          {/* Clear Session Button */}
          <div className="pt-2">
            <button
              onClick={onClearSession}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-md hover:bg-gray-200 transition-colors text-sm"
            >
              Clear Session
            </button>
            <p className="mt-2 text-xs text-gray-500 text-center">
              Refreshing the page will clear all data
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}

Sidebar.propTypes = {
  companyName: PropTypes.string,
  jobTitle: PropTypes.string,
  jobDescription: PropTypes.string,
  selectedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  isUploading: PropTypes.bool,
  isAnalyzing: PropTypes.bool,
  isAnalyzeLoading: PropTypes.bool,
  uploadError: PropTypes.string,
  canAnalyze: PropTypes.bool,
  onCompanyNameChange: PropTypes.func.isRequired,
  onJobTitleChange: PropTypes.func.isRequired,
  onJobDescriptionChange: PropTypes.func.isRequired,
  onFileSelect: PropTypes.func.isRequired,
  onRemoveFile: PropTypes.func.isRequired,
  onUpload: PropTypes.func.isRequired,
  onAnalyze: PropTypes.func.isRequired,
  onClearSession: PropTypes.func.isRequired,
}

export default Sidebar
