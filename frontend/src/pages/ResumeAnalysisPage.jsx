import Sidebar from '../components/Sidebar'
import AnalysisOutput from '../components/AnalysisOutput'
import ResumePreview from '../components/ResumePreview'

function ResumeAnalysisPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left sidebar */}
      <Sidebar />

      {/* Center analysis area */}
      <AnalysisOutput />

      {/* Right preview area */}
      <ResumePreview />
    </div>
  )
}

export default ResumeAnalysisPage
