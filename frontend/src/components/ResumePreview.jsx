import PropTypes from 'prop-types'

function ResumePreview({ sessionId, uploadedFile }) {
  // Props are reserved for future implementation
  void sessionId
  void uploadedFile

  return (
    <aside className="w-80 bg-white border-l border-gray-200 p-6 h-screen overflow-y-auto">
      <div className="text-gray-400 text-center">
        <p className="font-bold text-lg mb-2">Resume Preview</p>
        <p className="text-sm">TODO: To be implemented</p>
      </div>
    </aside>
  )
}

ResumePreview.propTypes = {
  sessionId: PropTypes.string,
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
}

export default ResumePreview
