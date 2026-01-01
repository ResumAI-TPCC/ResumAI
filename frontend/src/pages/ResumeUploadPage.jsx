import { useState } from 'react'
import FileUpload from '../components/FileUpload'

function ResumeUploadPage() {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileSelect = (file) => {
    setUploadedFile(file)
  }

  const handleUpload = async () => {
    if (!uploadedFile) return
    
    setIsUploading(true)
    // Simulate upload process
    setTimeout(() => {
      setIsUploading(false)
      // TODO: API call will be added here
      console.log('File uploaded:', uploadedFile)
    }, 1500)
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex flex-col">
      {/* Header */}
      <header className="w-full border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">ResumAI</h1>
            </div>
            <div className="text-sm text-gray-500">
              AI Resume Optimization Assistant
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-3xl">
          {/* Welcome Section */}
          {!uploadedFile && (
            <div className="text-center mb-12 animate-fade-in">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Upload Your Resume
              </h2>
              <p className="text-lg text-gray-600 mb-2">
                Let AI optimize your resume and boost your job search success
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF, DOCX, TXT formats, max 5MB
              </p>
            </div>
          )}

          {/* Upload Area */}
          <div className="mb-8">
            <FileUpload
              onFileSelect={handleFileSelect}
              uploadedFile={uploadedFile}
              onRemoveFile={handleRemoveFile}
            />
          </div>

          {/* Action Button */}
          {uploadedFile && (
            <div className="flex flex-col items-center gap-4 animate-fade-in">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="w-full max-w-md px-6 py-3.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isUploading ? (
                  <div className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Uploading...</span>
                  </div>
                ) : (
                  <span>Start Analysis</span>
                )}
              </button>
              
              <p className="text-xs text-gray-500 text-center">
                After upload, we'll provide professional resume analysis and optimization suggestions
              </p>
            </div>
          )}

          {/* Features */}
          {!uploadedFile && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 animate-fade-in">
              <div className="text-center p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Smart Analysis</h3>
                <p className="text-sm text-gray-600">
                  AI deeply analyzes resume content to identify areas for improvement
                </p>
              </div>

              <div className="text-center p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Job Matching</h3>
                <p className="text-sm text-gray-600">
                  Compare with job descriptions, calculate match score and provide suggestions
                </p>
              </div>

              <div className="text-center p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">One-Click Optimization</h3>
                <p className="text-sm text-gray-600">
                  Generate optimized resume with support for multiple export formats
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-gray-200 bg-white/50 backdrop-blur-sm py-4">
        <div className="max-w-4xl mx-auto px-6 text-center text-sm text-gray-500">
          <p>ResumAI - Make every resume outstanding</p>
        </div>
      </footer>
    </div>
  )
}

export default ResumeUploadPage

