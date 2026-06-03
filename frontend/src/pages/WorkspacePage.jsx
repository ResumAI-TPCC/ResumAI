import AppHeader from '../components/AppHeader.jsx'
import ResumeAnalysisPage from './ResumeAnalysisPage'

function WorkspacePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <AppHeader />
      <div className="flex-1 min-h-0">
        <ResumeAnalysisPage />
      </div>
    </div>
  )
}

export default WorkspacePage
