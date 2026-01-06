import PropTypes from 'prop-types'

function AnalysisOutput({ sessionId, jobDescription, companyName, jobTitle }) {
  // Props are reserved for future implementation
  void sessionId
  void jobDescription
  void companyName
  void jobTitle

  return (
    <main className="flex-1 p-8 bg-gray-50 overflow-y-auto">
      <div className="text-gray-400 text-center py-20">
        <p className="font-bold text-lg mb-2">Analysis Output</p>
        <p className="text-sm">TODO: To be implemented</p>
      </div>
    </main>
  )
}

AnalysisOutput.propTypes = {
  sessionId: PropTypes.string,
  jobDescription: PropTypes.string,
  companyName: PropTypes.string,
  jobTitle: PropTypes.string,
}

export default AnalysisOutput
