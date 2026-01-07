import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import AnalysisOutput from '../components/AnalysisOutput'
import ResumePreview from '../components/ResumePreview'
import { uploadResume } from '../utils/api'
import { saveSession, loadSession, clearSession as clearStorageSession } from '../utils/storage'

function ResumeAnalysisPage() {
  const [sessionId, setSessionId] = useState(null)
  const [companyName, setCompanyName] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  // Load session data on mount
  useEffect(() => {
    const session = loadSession()
    if (session) {
      setSessionId(session.session_id || null)
      setCompanyName(session.companyName || '')
      setJobTitle(session.jobTitle || '')
      setJobDescription(session.jobDescription || '')
      // Note: uploadedFile cannot be restored from localStorage, user needs to re-upload
    }
  }, [])

  const handleFileSelect = (file) => {
    setUploadError(null)
    setSelectedFile(file)
    // Reset uploaded file when new file is selected
    setUploadedFile(null)
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    
    setUploadError(null)
    
    try {
      setIsUploading(true)
      const response = await uploadResume(selectedFile)
      
      if (response.status === 'created' && response.data) {
        const newSessionId = response.data.session_id
        const expireAt = response.data.expire_at
        
        setSessionId(newSessionId)
        setUploadedFile(selectedFile)
        
        // Save session to localStorage only on upload success
        // Include current form values for session restore
        saveSession({
          session_id: newSessionId,
          expire_at: expireAt,
          companyName,
          jobTitle,
          jobDescription,
        })
      }
    } catch (error) {
      console.error('Upload error:', error)
      setUploadError(error.message || 'Failed to upload resume')
    } finally {
      setIsUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setUploadedFile(null)
    setSessionId(null)
  }

  // Simple state updates without localStorage writes
  // localStorage is only written on upload success or explicit save actions
  const handleCompanyNameChange = (value) => {
    setCompanyName(value)
  }

  const handleJobTitleChange = (value) => {
    setJobTitle(value)
  }

  const handleJobDescriptionChange = (value) => {
    setJobDescription(value)
  }

  const handleClearSession = () => {
    if (window.confirm('Are you sure you want to clear the session? All data will be lost.')) {
      clearStorageSession()
      setSessionId(null)
      setCompanyName('')
      setJobTitle('')
      setJobDescription('')
      setSelectedFile(null)
      setUploadedFile(null)
      setUploadError(null)
    }
  }

  return (
    <div className="h-screen bg-gray-50 flex overflow-hidden">
      {/* Left sidebar */}
      <Sidebar
        sessionId={sessionId}
        companyName={companyName}
        jobTitle={jobTitle}
        jobDescription={jobDescription}
        selectedFile={selectedFile}
        uploadedFile={uploadedFile}
        isUploading={isUploading}
        uploadError={uploadError}
        onCompanyNameChange={handleCompanyNameChange}
        onJobTitleChange={handleJobTitleChange}
        onJobDescriptionChange={handleJobDescriptionChange}
        onFileSelect={handleFileSelect}
        onRemoveFile={handleRemoveFile}
        onUpload={handleUpload}
        onClearSession={handleClearSession}
      />

      {/* Center analysis area */}
      <AnalysisOutput
        sessionId={sessionId}
        jobDescription={jobDescription}
        companyName={companyName}
        jobTitle={jobTitle}
      />

      {/* Right preview area */}
      <ResumePreview
        sessionId={sessionId}
        uploadedFile={uploadedFile}
      />
    </div>
  )
}

export default ResumeAnalysisPage
