import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [jobDescription, setJobDescription] = useState('')
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      setFile(files[0])
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      setFile(files[0])
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleStartOptimization = () => {
    // Navigate to workspace with file and job description data
    navigate('/workspace', { 
      state: { 
        file, 
        jdText: jobDescription 
      } 
    })
  }

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <h1>ResumAI</h1>
        <p className="subtitle">
          Transform your resume into a job-aligned professional document.
        </p>
      </section>

      {/* Main Interaction Area */}
      <section className="interaction-area">
        {/* Zone A: Resume Upload */}
        <div 
          className={`upload-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleUploadClick}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.docx,.doc,.txt"
            hidden
          />
          <div className="upload-icon">
            {file ? '✓' : '📄'}
          </div>
          <p className="upload-text">
            {file ? file.name : 'Drop your resume here or click to upload'}
          </p>
          <p className="upload-formats">
            Supported formats: PDF, DOCX, TXT
          </p>
        </div>

        {/* Zone B: Job Description */}
        <div className="jd-section">
          <label htmlFor="job-description" className="jd-label">
            Paste Job Description (Optional)
          </label>
          <textarea
            id="job-description"
            className="jd-textarea"
            placeholder="Paste the job description here to enable job-aligned optimization (Mode B)..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={6}
          />
          <p className="jd-hint">
            Adding a job description enables targeted resume optimization
          </p>
        </div>

        {/* Action Button */}
        <button 
          className="start-button"
          onClick={handleStartOptimization}
          disabled={!file}
        >
          Start Optimization
        </button>
      </section>
    </div>
  )
}

export default Home
