import { ENV } from './config/env'
import ResumeAnalysisPage from './pages/ResumeAnalysisPage'

function App() {
  return (
    <div className="h-screen flex flex-col">
      <ResumeAnalysisPage />
      <footer className="absolute bottom-2 right-4 z-10">
        <span className="text-xs text-gray-400">v{ENV.APP_VERSION}</span>
      </footer>
    </div>
  )
}

export default App
