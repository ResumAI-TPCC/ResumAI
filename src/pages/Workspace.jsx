import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState, useMemo } from 'react'
import './Workspace.css'

function Workspace() {
  const location = useLocation()
  const navigate = useNavigate()
  
  // Get state from location or fallback to sessionStorage (for testing)
  const { file, jdText } = useMemo(() => {
    if (location.state?.file) {
      return location.state
    }
    // Fallback for testing
    const stored = sessionStorage.getItem('mockWorkspaceState')
    if (stored) {
      return JSON.parse(stored)
    }
    return {}
  }, [location.state])
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: "Hello! I've analyzed your resume. What would you like to improve?"
    },
    {
      id: 2,
      type: 'user',
      content: "Make it stronger for a Product Manager role."
    }
  ])

  // Redirect to home if no file was provided
  useEffect(() => {
    if (!file) {
      navigate('/', { replace: true })
    }
  }, [file, navigate])

  const handleSendMessage = () => {
    if (!chatInput.trim()) return
    
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: 'user',
      content: chatInput.trim()
    }])
    setChatInput('')
    
    // Placeholder for AI response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'ai',
        content: "I'm processing your request. Backend integration coming soon!"
      }])
    }, 500)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleExportMarkdown = () => {
    // Placeholder for export functionality
    console.log('Exporting markdown...')
  }

  if (!file) {
    return null
  }

  const mode = jdText ? 'B (Job-Aligned)' : 'A (General)'

  return (
    <div className="workspace">
      {/* Left Panel - Resume Preview */}
      <div className="panel resume-panel">
        <div className="panel-header">
          <h2>Resume Preview</h2>
          <button className="export-btn" onClick={handleExportMarkdown}>
            Export Markdown
          </button>
        </div>
        
        <div className="panel-content resume-content">
          <div className="resume-paper">
            <p className="placeholder-text">Resume content will appear here...</p>
          </div>
        </div>
        
        <div className="panel-footer">
          <span className="debug-info">
            Loaded: {file.name} | Mode: {mode}
          </span>
        </div>
      </div>

      {/* Right Panel - AI Chat */}
      <div className="panel chat-panel">
        <div className="panel-header">
          <h2>ResumAI Assistant</h2>
          <span className="assistant-status">
            <span className="status-dot"></span>
            Online
          </span>
        </div>
        
        <div className="panel-content chat-content">
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.type}`}>
                <div className="message-avatar">
                  {msg.type === 'ai' ? '🤖' : '👤'}
                </div>
                <div className="message-bubble">
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="chat-input-area">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask ResumAI to improve your resume..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button 
            className="send-btn"
            onClick={handleSendMessage}
            disabled={!chatInput.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default Workspace
