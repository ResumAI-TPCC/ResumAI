import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import AnalysisOutput from '../components/AnalysisOutput'
import ResumePreview from '../components/ResumePreview'
import { uploadResume, optimizeResume, matchResumeWithJob } from '../utils/api'
import { saveSession, loadSession, clearSession as clearStorageSession } from '../utils/storage'

/**
 * ResumeAnalysisPage Component
 * 
 * Main page for resume analysis and optimization workflow
 * RA-20: Handles optimize resume logic
 */
function ResumeAnalysisPage() {
  const [sessionId, setSessionId] = useState(null)
  const [companyName, setCompanyName] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  
  // Optimize resume states
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizedFile, setOptimizedFile] = useState(null)
  const [optimizeError, setOptimizeError] = useState(null)
  const [matchScore, setMatchScore] = useState(null)

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
      setOptimizedFile(null)
      setMatchScore(null)
    }
  }

  /**
   * Handle optimize resume request
   * Calls the optimize API and stores the result
   */
  const handleOptimize = async () => {
    if (!sessionId) {
      setOptimizeError('Please upload a resume first')
      return
    }

    setIsOptimizing(true)
    setOptimizeError(null)

    try {
      const result = await optimizeResume(sessionId, jobDescription)
      
      if (result.status === 'ok' && result.data?.encoded_file) {
        // Store the optimized file
        setOptimizedFile({
          name: `optimized_resume_${new Date().getTime()}.pdf`,
          content: result.data.encoded_file,
        })
      } else {
        throw new Error('Invalid response from server')
      }
    } catch (error) {
      console.error('Optimize error:', error)
      setOptimizeError(error.message || 'Failed to optimize resume')
    } finally {
      setIsOptimizing(false)
    }
  }

  /**
   * Handle download of optimized resume
   * Decodes base64 and triggers browser download
   */
  const handleDownloadResume = () => {
    if (!optimizedFile?.content) {
      setOptimizeError('No optimized resume available')
      return
    }

    try {
      // Decode base64 to binary
      const byteCharacters = atob(optimizedFile.content)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)

      // Create blob and download
      const blob = new Blob([byteArray], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = optimizedFile.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      setOptimizeError('Failed to download resume')
    }
  }

  /**
   * Track match score from analysis output
   * This is called by AnalysisOutput when match analysis completes
   */
  const handleAnalysisComplete = (score) => {
    setMatchScore(score)
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
        onMatchScoreUpdate={handleAnalysisComplete}
      />
      <ResumePreview
        sessionId={sessionId}
        uploadedFile={uploadedFile}
        matchScore={matchScore}
        isOptimizing={isOptimizing}
        optimizedFile={optimizedFile}
        onOptimize={handleOptimize}
        onDownload={handleDownloadResume}
      />
    </div>
  )
}

export default ResumeAnalysisPage
