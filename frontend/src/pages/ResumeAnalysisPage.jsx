import Sidebar from '../components/Sidebar'
import MatchAnalysis from '../components/MatchAnalysis'
import ResumePreview from '../components/ResumePreview'

function ResumeAnalysisPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left sidebar */}
      <Sidebar />

      {/* Center analysis area */}
      <MatchAnalysis />

      {/* Right preview area */}
      <ResumePreview />
    </div>
  )
}

export default ResumeAnalysisPage
